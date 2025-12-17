#!/usr/bin/env python3
"""
Manual test script for rate limiting.

This script can be run against a live backend to verify rate limiting works.
Run the backend first: uvicorn app.main:app --reload

Then run this script: python tests/manual_rate_limit_test.py
"""
import requests
import time
from uuid import uuid4

BASE_URL = "http://localhost:8000"


def test_upload_rate_limit():
    """
    Test upload endpoint rate limiting (10/hour).

    Sends 11 requests and expects the 11th to be rate limited.
    """
    print("\n=== Testing Upload Endpoint Rate Limiting ===")
    print("Rate limit: 10 uploads per hour")
    print("Testing with 11 rapid requests...\n")

    patient_id = uuid4()

    for i in range(1, 12):
        # Create a dummy audio file
        files = {'file': ('test.mp3', b'dummy audio content', 'audio/mpeg')}
        params = {'patient_id': str(patient_id)}

        response = requests.post(
            f"{BASE_URL}/api/sessions/upload",
            params=params,
            files=files
        )

        print(f"Request {i}: Status {response.status_code}")

        if response.status_code == 429:
            print(f"  ✅ Rate limited! Response: {response.json()}")
            retry_after = response.json().get('retry_after', 'unknown')
            print(f"  Retry after: {retry_after} seconds")
            return True
        elif response.status_code in (400, 500):
            # Expected errors (no patient exists, etc.)
            print(f"  Expected error: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"  Response: {response.json()}")

        time.sleep(0.1)  # Small delay between requests

    print("  ❌ Rate limit not triggered after 11 requests!")
    return False


def test_extract_notes_rate_limit():
    """
    Test extract-notes endpoint rate limiting (20/hour).

    Sends 21 requests and expects the 21st to be rate limited.
    """
    print("\n=== Testing Extract Notes Endpoint Rate Limiting ===")
    print("Rate limit: 20 extractions per hour")
    print("Testing with 21 rapid requests...\n")

    session_id = uuid4()

    for i in range(1, 22):
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/extract-notes"
        )

        print(f"Request {i}: Status {response.status_code}")

        if response.status_code == 429:
            print(f"  ✅ Rate limited! Response: {response.json()}")
            retry_after = response.json().get('retry_after', 'unknown')
            print(f"  Retry after: {retry_after} seconds")
            return True
        elif response.status_code == 404:
            # Expected error (session doesn't exist)
            print(f"  Expected 404: Session not found")
        else:
            print(f"  Response: {response.json()}")

        time.sleep(0.1)  # Small delay between requests

    print("  ❌ Rate limit not triggered after 21 requests!")
    return False


def test_different_ips():
    """
    Verify that rate limits are per-IP (can't easily test without proxy).
    """
    print("\n=== Note on Per-IP Rate Limiting ===")
    print("Rate limits are applied per IP address using slowapi.")
    print("In production, this prevents individual users/IPs from exhausting quotas.")
    print("To test with multiple IPs, use different proxy servers or network interfaces.\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Rate Limiting Manual Test Suite")
    print("=" * 60)
    print("\nMake sure the backend is running:")
    print("  cd backend && uvicorn app.main:app --reload")
    print("")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Backend is running (status: {response.json().get('status')})\n")
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        print("Please start the backend first!\n")
        exit(1)

    # Run tests
    upload_passed = test_upload_rate_limit()
    extract_passed = test_extract_notes_rate_limit()
    test_different_ips()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Upload rate limiting: {'✅ PASS' if upload_passed else '❌ FAIL'}")
    print(f"Extract notes rate limiting: {'✅ PASS' if extract_passed else '❌ FAIL'}")
    print("")

    if upload_passed and extract_passed:
        print("✅ All rate limiting tests passed!")
    else:
        print("❌ Some tests failed. Check configuration.")
