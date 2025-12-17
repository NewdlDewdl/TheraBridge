"""
Test cases for exception handling middleware

Run with: pytest app/middleware/test_error_handler.py -v
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.error_handler import (
    register_exception_handlers,
    TranscriptionError,
    ExtractionError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)

# Create test app
app = FastAPI()
register_exception_handlers(app)


# Test endpoints that raise exceptions
@app.get("/test/transcription-error")
async def test_transcription_error():
    raise TranscriptionError(
        message="Test transcription failure",
        details={"file": "test.mp3"}
    )


@app.get("/test/extraction-error")
async def test_extraction_error():
    raise ExtractionError(
        message="Test extraction failure",
        user_message="Custom user message"
    )


@app.get("/test/database-error")
async def test_database_error():
    raise DatabaseError(
        message="Test database failure",
        retriable=False
    )


@app.get("/test/resource-not-found")
async def test_resource_not_found():
    raise ResourceNotFoundError(
        resource_type="Session",
        resource_id="123"
    )


@app.get("/test/validation-error")
async def test_validation_error():
    raise ValidationError(
        message="Invalid input",
        details={"field": "email", "error": "invalid format"}
    )


@app.get("/test/auth-error")
async def test_auth_error():
    raise AuthenticationError(
        message="Token expired"
    )


@app.get("/test/authz-error")
async def test_authz_error():
    raise AuthorizationError(
        message="Insufficient permissions"
    )


@app.get("/test/unhandled-error")
async def test_unhandled_error():
    raise ValueError("Unexpected error")


# Test client (raise_server_exceptions=False allows us to test error responses)
client = TestClient(app, raise_server_exceptions=False)


def test_transcription_error_response():
    """Test TranscriptionError returns proper structure"""
    response = client.get("/test/transcription-error")

    assert response.status_code == 500
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "TRANSCRIPTION_ERROR"
    assert data["error"]["retriable"] is True
    assert "request_id" in data["error"]
    assert data["error"]["details"]["file"] == "test.mp3"


def test_extraction_error_response():
    """Test ExtractionError returns custom user message"""
    response = client.get("/test/extraction-error")

    assert response.status_code == 500
    data = response.json()

    assert data["error"]["code"] == "EXTRACTION_ERROR"
    assert data["error"]["message"] == "Custom user message"
    assert data["error"]["retriable"] is True


def test_database_error_response():
    """Test DatabaseError with non-retriable flag"""
    response = client.get("/test/database-error")

    assert response.status_code == 500
    data = response.json()

    assert data["error"]["code"] == "DATABASE_ERROR"
    assert data["error"]["retriable"] is False


def test_resource_not_found_response():
    """Test ResourceNotFoundError returns 404"""
    response = client.get("/test/resource-not-found")

    assert response.status_code == 404
    data = response.json()

    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert data["error"]["retriable"] is False
    assert data["error"]["details"]["resource_type"] == "Session"
    assert data["error"]["details"]["resource_id"] == "123"


def test_validation_error_response():
    """Test ValidationError returns 422"""
    response = client.get("/test/validation-error")

    assert response.status_code == 422
    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["retriable"] is False
    assert "field" in data["error"]["details"]


def test_authentication_error_response():
    """Test AuthenticationError returns 401"""
    response = client.get("/test/auth-error")

    assert response.status_code == 401
    data = response.json()

    assert data["error"]["code"] == "AUTHENTICATION_ERROR"
    assert data["error"]["retriable"] is False


def test_authorization_error_response():
    """Test AuthorizationError returns 403"""
    response = client.get("/test/authz-error")

    assert response.status_code == 403
    data = response.json()

    assert data["error"]["code"] == "AUTHORIZATION_ERROR"
    assert data["error"]["retriable"] is False


def test_unhandled_error_response():
    """Test unhandled exceptions return generic error"""
    response = client.get("/test/unhandled-error")

    assert response.status_code == 500
    data = response.json()

    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["retriable"] is True
    # User message should be generic and safe
    assert "unexpected" in data["error"]["message"].lower() or "occurred" in data["error"]["message"].lower()
    # Internal error details should NOT be exposed in message
    assert "ValueError" not in data["error"]["message"]


def test_all_errors_have_request_id():
    """Test that all errors include unique request_id"""
    endpoints = [
        "/test/transcription-error",
        "/test/extraction-error",
        "/test/database-error",
        "/test/resource-not-found",
    ]

    request_ids = set()
    for endpoint in endpoints:
        response = client.get(endpoint)
        data = response.json()
        request_id = data["error"]["request_id"]

        assert request_id is not None
        assert isinstance(request_id, str)
        assert len(request_id) > 0

        # Ensure request IDs are unique
        assert request_id not in request_ids
        request_ids.add(request_id)


def test_error_structure_consistency():
    """Test that all errors follow consistent structure"""
    response = client.get("/test/transcription-error")
    data = response.json()

    # Required fields
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "retriable" in data["error"]
    assert "request_id" in data["error"]

    # Type checks
    assert isinstance(data["error"]["code"], str)
    assert isinstance(data["error"]["message"], str)
    assert isinstance(data["error"]["retriable"], bool)
    assert isinstance(data["error"]["request_id"], str)


if __name__ == "__main__":
    # Run basic smoke test
    print("Running smoke tests...")

    tests = [
        ("Transcription Error", test_transcription_error_response),
        ("Extraction Error", test_extraction_error_response),
        ("Database Error", test_database_error_response),
        ("Resource Not Found", test_resource_not_found_response),
        ("Validation Error", test_validation_error_response),
        ("Authentication Error", test_authentication_error_response),
        ("Authorization Error", test_authorization_error_response),
        ("Unhandled Error", test_unhandled_error_response),
        ("Request ID Uniqueness", test_all_errors_have_request_id),
        ("Structure Consistency", test_error_structure_consistency),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}: Unexpected error - {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
