"""
Structured logging configuration for TherapyBridge backend.

Provides JSON-formatted logging with request context, timestamps, and
proper log levels for aggregation and monitoring.
"""
import logging
import sys
from datetime import datetime
from typing import Optional
import json
from contextvars import ContextVar


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format for easy parsing
    by log aggregation tools (CloudWatch, Datadog, etc.).

    Automatically includes request_id from context if available.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Automatically add request_id from context if not explicitly provided
        if not hasattr(record, "request_id"):
            try:
                from app.middleware.correlation_id import get_request_id
                request_id = get_request_id()
                if request_id:
                    log_data["request_id"] = request_id
            except ImportError:
                # Middleware not yet imported (e.g., during startup)
                pass

        # Add extra fields if present (e.g., request_id, session_id)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "patient_id"):
            log_data["patient_id"] = record.patient_id
        if hasattr(record, "file_size_mb"):
            log_data["file_size_mb"] = record.file_size_mb
        if hasattr(record, "duration_seconds"):
            log_data["duration_seconds"] = record.duration_seconds

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = False
) -> None:
    """
    Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON formatter; if False, use human-readable format

    Usage:
        # In main.py or at app startup:
        setup_logging(log_level="INFO", json_format=True)  # Production
        setup_logging(log_level="DEBUG", json_format=False)  # Development
    """
    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Logger instance configured with application settings

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing session", extra={"session_id": str(session_id)})
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds request context to all log messages.

    Usage:
        logger = LoggerAdapter(get_logger(__name__), {"request_id": request_id})
        logger.info("Processing started")  # Will include request_id automatically
    """

    def process(self, msg, kwargs):
        """Add extra context to log record"""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs
