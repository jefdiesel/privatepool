"""Rate limiting middleware using Redis sliding window."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.redis_service import get_redis_client


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule."""

    requests: int
    window_seconds: int
    key_prefix: str = "ratelimit"


class RateLimiter:
    """Redis-based sliding window rate limiter."""

    # Default rate limits by endpoint pattern
    DEFAULT_LIMITS = {
        "/api/auth/verify": RateLimitConfig(requests=10, window_seconds=60),
        "/api/auth/": RateLimitConfig(requests=30, window_seconds=60),
        "/api/tournaments": RateLimitConfig(requests=30, window_seconds=60),
        "/api/admin/": RateLimitConfig(requests=60, window_seconds=60),
        "/api/": RateLimitConfig(requests=100, window_seconds=60),  # Default for API
    }

    # Authenticated users get higher limits
    AUTHENTICATED_MULTIPLIER = 3

    def __init__(self, custom_limits: dict[str, RateLimitConfig] | None = None):
        """Initialize rate limiter.

        Args:
            custom_limits: Optional custom rate limit configurations
        """
        self.limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self.limits.update(custom_limits)

    def _get_limit_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for a path.

        Args:
            path: Request path

        Returns:
            Rate limit configuration
        """
        # Check for exact match first
        if path in self.limits:
            return self.limits[path]

        # Check for prefix match (longest match wins)
        matching_prefixes = [
            (prefix, config)
            for prefix, config in self.limits.items()
            if path.startswith(prefix)
        ]
        if matching_prefixes:
            # Sort by prefix length descending to get longest match
            matching_prefixes.sort(key=lambda x: len(x[0]), reverse=True)
            return matching_prefixes[0][1]

        # Default fallback
        return RateLimitConfig(requests=100, window_seconds=60)

    async def is_allowed(
        self,
        key: str,
        path: str,
        is_authenticated: bool = False,
    ) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., IP address or user ID)
            path: Request path
            is_authenticated: Whether user is authenticated

        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        config = self._get_limit_config(path)
        max_requests = config.requests
        if is_authenticated:
            max_requests *= self.AUTHENTICATED_MULTIPLIER

        redis = await get_redis_client()
        if redis is None:
            # If Redis is unavailable, allow the request
            return True, {}

        now = time.time()
        window_start = now - config.window_seconds
        rate_key = f"{config.key_prefix}:{key}:{path}"

        try:
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(rate_key, 0, window_start)

            # Count current requests in window
            pipe.zcard(rate_key)

            # Add current request
            pipe.zadd(rate_key, {str(now): now})

            # Set expiry on the key
            pipe.expire(rate_key, config.window_seconds + 1)

            results = await pipe.execute()
            current_count = results[1]

            # Calculate headers
            remaining = max(0, max_requests - current_count - 1)
            reset_time = int(now + config.window_seconds)

            headers = {
                "X-RateLimit-Limit": max_requests,
                "X-RateLimit-Remaining": remaining,
                "X-RateLimit-Reset": reset_time,
            }

            if current_count >= max_requests:
                headers["Retry-After"] = config.window_seconds
                return False, headers

            return True, headers

        except Exception:
            # On Redis error, allow the request
            return True, {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter | None = None,
        key_func: Callable[[Request], str] | None = None,
        exclude_paths: list[str] | None = None,
    ):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limiter: Rate limiter instance
            key_func: Function to extract rate limit key from request
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or ["/api/health", "/api/docs", "/api/openapi.json"]

    def _default_key_func(self, request: Request) -> str:
        """Extract rate limit key from request.

        Uses X-Forwarded-For header if present (for proxied requests),
        otherwise falls back to client IP.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiting."""
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Get rate limit key
        key = self.key_func(request)

        # Check if authenticated (look for Authorization header)
        is_authenticated = "Authorization" in request.headers

        # Check rate limit
        is_allowed, headers = await self.rate_limiter.is_allowed(
            key=key,
            path=path,
            is_authenticated=is_authenticated,
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": headers.get("Retry-After", 60),
                },
                headers={k: str(v) for k, v in headers.items()},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for header, value in headers.items():
            response.headers[header] = str(value)

        return response
