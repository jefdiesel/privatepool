"""Correlation ID middleware for request tracing."""

from __future__ import annotations

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import set_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation IDs to requests for distributed tracing.

    - Extracts correlation ID from X-Correlation-ID header if present
    - Generates a new correlation ID if not present
    - Adds correlation ID to response headers
    - Sets correlation ID in logging context
    """

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation ID."""
        # Get or generate correlation ID
        correlation_id = request.headers.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:8]

        # Set in logging context
        set_correlation_id(correlation_id)

        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response
        response.headers[self.HEADER_NAME] = correlation_id

        return response
