"""Security headers middleware."""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses.

    Implements OWASP recommended security headers:
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        app,
        csp_policy: str | None = None,
        hsts_max_age: int = 31536000,  # 1 year
        enable_hsts: bool = True,
    ):
        """Initialize security headers middleware.

        Args:
            app: FastAPI application
            csp_policy: Custom Content-Security-Policy header value
            hsts_max_age: Max age for HSTS header in seconds
            enable_hsts: Whether to enable HSTS (disable for development)
        """
        super().__init__(app)
        self.csp_policy = csp_policy or self._default_csp()
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts

    def _default_csp(self) -> str:
        """Generate default Content-Security-Policy."""
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Needed for some frontend frameworks
            "style-src 'self' 'unsafe-inline'",  # Needed for inline styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' wss: https:",  # Allow WebSocket and API connections
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # HSTS (only in production)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )

        return response
