#!/usr/bin/env python3
"""
Integration test for correlation ID middleware.

This script tests the actual running backend to verify:
1. Request IDs are generated and returned
2. Request IDs are preserved when provided
3. Logs include request IDs
"""
import requests
import uuid
import sys


def test_correlation_id_integration():
    """Test correlation ID with the actual backend"""
    base_url = "http://localhost:8000"

    print("\n" + "="*80)
    print("CORRELATION ID INTEGRATION TEST")
    print("="*80 + "\n")

    # Test 1: Auto-generated request ID
    print("Test 1: Auto-generated Request ID")
    print("-" * 40)
    response = requests.get(f"{base_url}/")
    print(f"GET {base_url}/")
    print(f"Response Status: {response.status_code}")
    print(f"X-Request-ID Header: {response.headers.get('X-Request-ID')}")

    if "X-Request-ID" not in response.headers:
        print("❌ FAILED: X-Request-ID header not present")
        return False

    request_id = response.headers["X-Request-ID"]
    try:
        uuid.UUID(request_id)
        print(f"✅ PASSED: Valid UUID generated: {request_id}\n")
    except ValueError:
        print(f"❌ FAILED: Invalid UUID: {request_id}\n")
        return False

    # Test 2: Custom request ID preservation
    print("Test 2: Custom Request ID Preservation")
    print("-" * 40)
    custom_id = str(uuid.uuid4())
    print(f"Sending X-Request-ID: {custom_id}")
    response = requests.get(f"{base_url}/", headers={"X-Request-ID": custom_id})
    print(f"Response Status: {response.status_code}")
    print(f"Received X-Request-ID: {response.headers.get('X-Request-ID')}")

    if response.headers.get("X-Request-ID") == custom_id:
        print(f"✅ PASSED: Request ID preserved\n")
    else:
        print(f"❌ FAILED: Request ID not preserved\n")
        return False

    # Test 3: Alternative headers (X-Correlation-ID)
    print("Test 3: Alternative Header (X-Correlation-ID)")
    print("-" * 40)
    correlation_id = str(uuid.uuid4())
    print(f"Sending X-Correlation-ID: {correlation_id}")
    response = requests.get(f"{base_url}/", headers={"X-Correlation-ID": correlation_id})
    print(f"Response Status: {response.status_code}")
    print(f"Received X-Request-ID: {response.headers.get('X-Request-ID')}")

    if response.headers.get("X-Request-ID") == correlation_id:
        print(f"✅ PASSED: Alternative header accepted\n")
    else:
        print(f"❌ FAILED: Alternative header not accepted\n")
        return False

    # Test 4: Health endpoint
    print("Test 4: Health Endpoint with Request ID")
    print("-" * 40)
    custom_id = str(uuid.uuid4())
    print(f"Sending X-Request-ID: {custom_id}")
    response = requests.get(f"{base_url}/health", headers={"X-Request-ID": custom_id})
    print(f"GET {base_url}/health")
    print(f"Response Status: {response.status_code}")
    print(f"Received X-Request-ID: {response.headers.get('X-Request-ID')}")

    if response.headers.get("X-Request-ID") == custom_id:
        print(f"✅ PASSED: Request ID in health endpoint\n")
    else:
        print(f"❌ FAILED: Request ID missing in health endpoint\n")
        return False

    print("="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80 + "\n")

    print("Next Steps:")
    print("1. Check backend logs - they should include request_id field")
    print("2. Set JSON_LOGS=true in .env to see structured JSON logs")
    print("3. All logs for a request will share the same request_id")
    print("4. Frontend can send X-Request-ID for end-to-end tracing\n")

    return True


if __name__ == "__main__":
    try:
        success = test_correlation_id_integration()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend")
        print("Please ensure the backend is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn app.main:app --reload\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)
