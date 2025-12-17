"""
Correlation ID middleware for distributed tracing.

Generates or accepts a unique request ID for each HTTP request, enabling
end-to-end request tracing across services and log correlation.

Features:
- Accepts X-Request-ID header from client/upstream proxy
- Generates UUID if no request ID provided
- Stores ID in context variable for access throughout request lifecycle
- Adds X-Request-ID to response headers
- Thread-safe using contextvars
"""
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for storing request ID (thread-safe)
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Request ID string or None if not set

    Usage:
        # In any endpoint or service:
        from app.middleware.correlation_id import get_request_id

        request_id = get_request_id()
        logger.info("Processing request", extra={"request_id": request_id})
    """
    return request_id_context.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation ID tracking to all requests.

    Request Flow:
    1. Check for X-Request-ID header in incoming request
    2. Generate UUID if header not present
    3. Store ID in context variable (accessible throughout request)
    4. Add X-Request-ID to response headers
    5. Clear context after response (automatic via context manager)

    Header Names:
    - X-Request-ID: Standard correlation ID header
    - Also checks X-Correlation-ID as alternative
    """

    def __init__(self, app, header_name: str = "X-Request-ID"):
        """
        Initialize correlation ID middleware.

        Args:
            app: FastAPI application instance
            header_name: Name of header to use for request ID (default: X-Request-ID)
        """
        super().__init__(app)
        self.header_name = header_name
        self.alternative_headers = ["X-Correlation-ID", "X-Trace-ID"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject correlation ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            HTTP response with X-Request-ID header
        """
        # Try to get request ID from headers (case-insensitive)
        request_id = request.headers.get(self.header_name.lower())

        # Fall back to alternative headers if not found
        if not request_id:
            for alt_header in self.alternative_headers:
                request_id = request.headers.get(alt_header.lower())
                if request_id:
                    break

        # Generate new UUID if no request ID provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in context variable (accessible to all code in request scope)
        request_id_context.set(request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers for client-side tracing
        response.headers[self.header_name] = request_id

        return response


__all__ = ['CorrelationIdMiddleware', 'get_request_id', 'request_id_context']
