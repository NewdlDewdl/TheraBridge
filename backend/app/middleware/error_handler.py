"""
Global exception handling middleware for TherapyBridge API

Provides:
- Custom exception classes with error classification
- Structured error responses with request tracking
- Global exception handler registration
- User-friendly error messages
- Retriable error flagging
"""
import uuid
import logging
from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================

class AppException(Exception):
    """Base application exception with structured error metadata"""

    def __init__(
        self,
        message: str,
        error_code: str,
        user_message: Optional[str] = None,
        retriable: bool = False,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or message
        self.retriable = retriable
        self.status_code = status_code
        self.details = details or {}


class SessionProcessingError(AppException):
    """Base exception for session processing errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "SESSION_PROCESSING_ERROR",
        user_message: Optional[str] = None,
        retriable: bool = True,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            user_message=user_message or "Failed to process therapy session. Please try again.",
            retriable=retriable,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class TranscriptionError(SessionProcessingError):
    """Raised when audio transcription fails"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = True,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="TRANSCRIPTION_ERROR",
            user_message=user_message or "Failed to transcribe audio file. Please ensure the file is a valid audio format and try again.",
            retriable=retriable,
            details=details
        )


class ExtractionError(SessionProcessingError):
    """Raised when AI note extraction fails"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = True,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="EXTRACTION_ERROR",
            user_message=user_message or "Failed to extract therapy notes from transcript. Please try again.",
            retriable=retriable,
            details=details
        )


class DatabaseError(AppException):
    """Raised when database operations fail"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = True,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            user_message=user_message or "A database error occurred. Please try again later.",
            retriable=retriable,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ValidationError(AppException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = False,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            user_message=user_message or "Invalid input data. Please check your request and try again.",
            retriable=retriable,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationError(AppException):
    """Raised when authentication fails"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = False,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            user_message=user_message or "Authentication failed. Please log in and try again.",
            retriable=retriable,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(AppException):
    """Raised when user lacks required permissions"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        retriable: bool = False,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            user_message=user_message or "You do not have permission to access this resource.",
            retriable=retriable,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundError(AppException):
    """Raised when requested resource does not exist"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        user_message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            user_message=user_message or f"The requested {resource_type.lower()} was not found.",
            retriable=False,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"resource_type": resource_type, "resource_id": resource_id}
        )


# ============================================================================
# Error Response Builder
# ============================================================================

def create_error_response(
    request: Request,
    error_code: str,
    user_message: str,
    status_code: int,
    retriable: bool = False,
    details: Optional[dict] = None,
    internal_message: Optional[str] = None
) -> JSONResponse:
    """
    Create structured error response

    Args:
        request: FastAPI request object
        error_code: Machine-readable error code (e.g., "TRANSCRIPTION_ERROR")
        user_message: Human-readable message safe to display to users
        status_code: HTTP status code
        retriable: Whether the client should retry the request
        details: Additional error context (sanitized for client)
        internal_message: Internal error message (logged, not sent to client)

    Returns:
        JSONResponse with structured error data
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())

    # Log error with internal details
    log_message = f"[{request_id}] {error_code}: {internal_message or user_message}"
    if details:
        log_message += f" | Details: {details}"

    if status_code >= 500:
        logger.error(log_message)
    else:
        logger.warning(log_message)

    # Build client-safe error response
    error_response = {
        "error": {
            "code": error_code,
            "message": user_message,
            "retriable": retriable,
            "request_id": request_id,
        }
    }

    # Add sanitized details if provided
    if details:
        error_response["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


# ============================================================================
# Global Exception Handlers
# ============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    return create_error_response(
        request=request,
        error_code=exc.error_code,
        user_message=exc.user_message,
        status_code=exc.status_code,
        retriable=exc.retriable,
        details=exc.details,
        internal_message=exc.message
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions from FastAPI/Starlette"""
    # Map common HTTP status codes to user-friendly messages
    user_messages = {
        400: "Invalid request. Please check your input and try again.",
        401: "Authentication required. Please log in.",
        403: "You do not have permission to access this resource.",
        404: "The requested resource was not found.",
        405: "This operation is not allowed.",
        409: "Request conflicts with current server state.",
        429: "Too many requests. Please try again later.",
        500: "An internal server error occurred. Please try again later.",
        503: "Service temporarily unavailable. Please try again later.",
    }

    user_message = user_messages.get(exc.status_code, str(exc.detail))

    return create_error_response(
        request=request,
        error_code=f"HTTP_{exc.status_code}",
        user_message=user_message,
        status_code=exc.status_code,
        retriable=exc.status_code in [408, 429, 500, 502, 503, 504],
        internal_message=str(exc.detail)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors from Pydantic"""
    # Extract field-level validation errors
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })

    return create_error_response(
        request=request,
        error_code="VALIDATION_ERROR",
        user_message="Invalid request data. Please check the highlighted fields.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        retriable=False,
        details={"validation_errors": validation_errors},
        internal_message=f"Request validation failed: {validation_errors}"
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions (last resort fallback)"""
    # Log full exception with stack trace
    logger.exception(f"Unhandled exception in {request.method} {request.url.path}")

    # Never expose internal error details to clients
    return create_error_response(
        request=request,
        error_code="INTERNAL_SERVER_ERROR",
        user_message="An unexpected error occurred. Our team has been notified.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        retriable=True,
        internal_message=f"{type(exc).__name__}: {str(exc)}"
    )


# ============================================================================
# Registration Helper
# ============================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app

    Usage in main.py:
        from app.middleware.error_handler import register_exception_handlers
        register_exception_handlers(app)
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("✅ Global exception handlers registered")
