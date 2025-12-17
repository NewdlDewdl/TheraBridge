"""
Middleware components for TherapyBridge API
"""
from app.middleware.rate_limit import limiter, custom_rate_limit_handler
from app.middleware.correlation_id import (
    CorrelationIdMiddleware,
    get_request_id,
    request_id_context
)
from app.middleware.error_handler import (
    register_exception_handlers,
    AppException,
    SessionProcessingError,
    TranscriptionError,
    ExtractionError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
)

__all__ = [
    'limiter',
    'custom_rate_limit_handler',
    'CorrelationIdMiddleware',
    'get_request_id',
    'request_id_context',
    'register_exception_handlers',
    'AppException',
    'SessionProcessingError',
    'TranscriptionError',
    'ExtractionError',
    'DatabaseError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'ResourceNotFoundError',
]
