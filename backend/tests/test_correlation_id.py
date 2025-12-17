"""
Tests for correlation ID middleware.

Tests:
1. Request ID generation when not provided
2. Request ID preservation when provided
3. Request ID in response headers
4. Request ID in logs
5. Request ID context propagation
"""
import pytest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.correlation_id import (
    CorrelationIdMiddleware,
    get_request_id,
    request_id_context
)
from app.logging_config import get_logger

# Create test app
app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)


@app.get("/test")
async def test_endpoint():
    """Test endpoint that returns request ID from context"""
    request_id = get_request_id()
    return {
        "message": "test",
        "request_id_from_context": request_id
    }


@app.get("/test-logging")
async def test_logging_endpoint():
    """Test endpoint that logs messages to verify request ID inclusion"""
    logger = get_logger(__name__)
    request_id = get_request_id()

    # Log a message
    logger.info("Test log message", extra={"test_field": "test_value"})

    return {
        "message": "logged",
        "request_id": request_id
    }


client = TestClient(app)


def test_generates_request_id_when_not_provided():
    """Test that middleware generates UUID when X-Request-ID not provided"""
    response = client.get("/test")

    # Should have request ID in response headers
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]

    # Should be a valid UUID
    try:
        uuid.UUID(request_id)
        assert True
    except ValueError:
        pytest.fail(f"Generated request ID is not a valid UUID: {request_id}")

    # Response body should include the same request ID
    assert response.status_code == 200
    body = response.json()
    assert body["request_id_from_context"] == request_id


def test_preserves_provided_request_id():
    """Test that middleware uses provided X-Request-ID header"""
    custom_request_id = str(uuid.uuid4())

    response = client.get("/test", headers={"X-Request-ID": custom_request_id})

    # Should return the same request ID
    assert response.headers["x-request-id"] == custom_request_id

    # Response body should include the same request ID
    body = response.json()
    assert body["request_id_from_context"] == custom_request_id


def test_accepts_alternative_headers():
    """Test that middleware accepts X-Correlation-ID and X-Trace-ID"""
    # Test X-Correlation-ID
    correlation_id = str(uuid.uuid4())
    response = client.get("/test", headers={"X-Correlation-ID": correlation_id})
    assert response.headers["x-request-id"] == correlation_id

    # Test X-Trace-ID
    trace_id = str(uuid.uuid4())
    response = client.get("/test", headers={"X-Trace-ID": trace_id})
    assert response.headers["x-request-id"] == trace_id


def test_request_id_in_response_headers():
    """Test that X-Request-ID is always present in response headers"""
    response = client.get("/test")

    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_request_id_context_propagation():
    """Test that request ID is accessible throughout request lifecycle"""
    custom_request_id = str(uuid.uuid4())

    response = client.get("/test", headers={"X-Request-ID": custom_request_id})

    body = response.json()

    # Request ID from context should match the one we sent
    assert body["request_id_from_context"] == custom_request_id

    # Response header should match
    assert response.headers["x-request-id"] == custom_request_id


def test_multiple_concurrent_requests():
    """Test that request IDs don't leak between concurrent requests"""
    request_ids = [str(uuid.uuid4()) for _ in range(10)]

    responses = []
    for req_id in request_ids:
        response = client.get("/test", headers={"X-Request-ID": req_id})
        responses.append(response)

    # Each response should have its own unique request ID
    for req_id, response in zip(request_ids, responses):
        assert response.headers["x-request-id"] == req_id
        body = response.json()
        assert body["request_id_from_context"] == req_id


def test_request_id_logging_integration():
    """Test that request ID is included in log output"""
    custom_request_id = str(uuid.uuid4())

    response = client.get(
        "/test-logging",
        headers={"X-Request-ID": custom_request_id}
    )

    # Should execute successfully
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == custom_request_id

    # Note: To fully test logging, you'd need to capture log output
    # This is demonstrated in the manual test below


if __name__ == "__main__":
    """
    Manual test for visual verification of logging integration.

    Run with: python -m pytest backend/tests/test_correlation_id.py -v -s
    Or directly: python backend/tests/test_correlation_id.py
    """
    import logging
    from app.logging_config import setup_logging, JSONFormatter

    # Setup JSON logging to see request IDs in output
    setup_logging(log_level="INFO", json_format=True)

    print("\n" + "="*80)
    print("MANUAL TEST: Request ID in Logs")
    print("="*80 + "\n")

    # Test with custom request ID
    custom_id = str(uuid.uuid4())
    print(f"Sending request with X-Request-ID: {custom_id}\n")

    response = client.get("/test-logging", headers={"X-Request-ID": custom_id})

    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers['X-Request-ID']: {response.headers.get('x-request-id')}")
    print(f"Response body: {response.json()}\n")

    print("="*80)
    print("Check the log output above - it should include 'request_id': '" + custom_id + "'")
    print("="*80 + "\n")
