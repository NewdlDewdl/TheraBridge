#!/usr/bin/env python3
"""
Example demonstrating correlation ID usage in backend endpoints.

This file shows best practices for using request correlation IDs
for distributed tracing and log correlation.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.middleware.correlation_id import get_request_id
from app.database import get_db
from app.logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)

router = APIRouter()


# Example 1: Basic endpoint with automatic request ID logging
@router.get("/example/basic")
async def basic_example():
    """
    Simple endpoint demonstrating automatic request ID inclusion.

    The request ID is automatically included in all log messages
    when using JSON logging format (JSON_LOGS=true).
    """
    # Log messages automatically include request_id from context
    logger.info("Processing basic request")

    return {"message": "success"}


# Example 2: Accessing request ID explicitly
@router.get("/example/explicit")
async def explicit_request_id():
    """
    Endpoint demonstrating explicit request ID access.

    Useful when you need the request ID for:
    - Including in response payload
    - Forwarding to external services
    - Custom error messages
    """
    # Get request ID from context
    request_id = get_request_id()

    logger.info(f"Handling request {request_id}")

    # Can include in response if needed
    return {
        "message": "success",
        "request_id": request_id
    }


# Example 3: Database operations with request tracing
@router.post("/example/database")
async def database_example(db: AsyncSession = Depends(get_db)):
    """
    Endpoint demonstrating request ID in database operations.

    All logs related to this database operation will share
    the same request_id, making it easy to trace the full flow.
    """
    request_id = get_request_id()

    logger.info("Starting database operation", extra={
        "operation": "create_record"
    })

    try:
        # Simulate database operation
        # In real code, this would be actual SQLAlchemy operations
        logger.info("Database query executed successfully", extra={
            "rows_affected": 1
        })

        return {"message": "success", "request_id": request_id}

    except Exception as e:
        logger.error("Database operation failed", extra={
            "error": str(e),
            "operation": "create_record"
        }, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=f"Database error (request_id: {request_id})"
        )


# Example 4: Multi-step process with detailed logging
@router.post("/example/process")
async def multi_step_process():
    """
    Complex endpoint with multiple steps, each logged with request ID.

    Demonstrates how all steps in a request flow share the same
    request_id, making it easy to trace the entire process.
    """
    request_id = get_request_id()

    # Step 1: Validation
    logger.info("Step 1: Validating input", extra={"step": 1})

    # Step 2: Processing
    logger.info("Step 2: Processing data", extra={"step": 2})

    # Step 3: External service call
    logger.info("Step 3: Calling external service", extra={
        "step": 3,
        "service": "transcription_api"
    })

    # If calling external service, forward the request ID
    # external_headers = {"X-Request-ID": request_id}
    # response = await httpx.post(url, headers=external_headers)

    # Step 4: Finalizing
    logger.info("Step 4: Finalizing response", extra={"step": 4})

    return {
        "message": "Process complete",
        "request_id": request_id,
        "steps_completed": 4
    }


# Example 5: Error handling with request ID
@router.get("/example/error")
async def error_example():
    """
    Endpoint demonstrating error handling with request IDs.

    When errors occur, the request_id helps correlate:
    - Frontend error logs
    - Backend error logs
    - External service logs
    - Database errors
    """
    request_id = get_request_id()

    try:
        logger.info("Attempting risky operation")

        # Simulate error
        raise ValueError("Simulated error for demonstration")

    except ValueError as e:
        # Log error with full context
        logger.error("Operation failed", extra={
            "error_type": "ValueError",
            "error_message": str(e)
        }, exc_info=True)

        # Return error with request ID for client-side correlation
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Operation failed",
                "request_id": request_id,
                "message": "Check server logs for details"
            }
        )


# Example 6: Background task with request ID propagation
@router.post("/example/background")
async def background_task_example():
    """
    Endpoint demonstrating request ID in background tasks.

    IMPORTANT: Background tasks run outside the request context,
    so request_id won't be automatically available. You need to
    capture it and pass it explicitly.
    """
    # Capture request ID before starting background task
    request_id = get_request_id()

    logger.info("Starting background task", extra={
        "task_type": "async_processing"
    })

    # In a real background task, you'd pass request_id as a parameter
    # background_tasks.add_task(process_file, file_path, request_id=request_id)

    return {
        "message": "Background task queued",
        "request_id": request_id
    }


def process_file_background(file_path: str, request_id: str):
    """
    Background task that receives request_id as parameter.

    Since background tasks don't have access to request context,
    pass request_id explicitly and include in log messages.
    """
    # Manually include request_id in logs for background tasks
    logger.info("Background task started", extra={
        "request_id": request_id,  # Explicitly add
        "file_path": file_path
    })

    try:
        # Process file...
        logger.info("Background task completed", extra={
            "request_id": request_id,
            "file_path": file_path
        })
    except Exception as e:
        logger.error("Background task failed", extra={
            "request_id": request_id,
            "file_path": file_path,
            "error": str(e)
        }, exc_info=True)


# Example log output with JSON_LOGS=true:
"""
{
  "timestamp": "2025-12-17T10:30:15.123456",
  "level": "INFO",
  "logger": "app.routers.example",
  "message": "Step 1: Validating input",
  "module": "example",
  "function": "multi_step_process",
  "line": 95,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "step": 1
}
{
  "timestamp": "2025-12-17T10:30:16.234567",
  "level": "INFO",
  "logger": "app.routers.example",
  "message": "Step 2: Processing data",
  "module": "example",
  "function": "multi_step_process",
  "line": 98,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "step": 2
}
{
  "timestamp": "2025-12-17T10:30:17.345678",
  "level": "INFO",
  "logger": "app.routers.example",
  "message": "Step 3: Calling external service",
  "module": "example",
  "function": "multi_step_process",
  "line": 101,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "step": 3,
  "service": "transcription_api"
}

Notice: All logs share the same request_id!
"""

# Best Practices Summary:
"""
✅ DO:
- Use get_logger(__name__) for structured logging
- Let request_id be automatically included in logs (JSON format)
- Include request_id in error responses for client correlation
- Forward request_id to external services via X-Request-ID header
- Capture request_id before starting background tasks
- Add contextual data via extra={} parameter

❌ DON'T:
- Don't manually add request_id to every log (it's automatic)
- Don't use request_id as authentication/authorization token
- Don't assume request_id is available in background tasks (pass explicitly)
- Don't forget to enable JSON_LOGS=true in production
"""
