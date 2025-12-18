"""
Pytest fixtures for router integration tests.

IMPORTANT: This file intentionally does NOT define duplicate fixtures.
All standard fixtures (test_db, client, therapist_user, patient_user, etc.)
are defined in the main tests/conftest.py file.

This file is reserved for router-specific fixtures that are ONLY used
by tests in the tests/routers/ directory.
"""
# CRITICAL: Set SECRET_KEY BEFORE any imports that load auth_config
import os
os.environ["SECRET_KEY"] = "test-secret-key-must-be-32-characters-long-for-hs256-algorithm-security"

# Router-specific fixtures can be added here as needed
# DO NOT duplicate fixtures from tests/conftest.py
