"""
Test rate limiting on extraction endpoints
"""
import pytest
from app.routers import sessions
from app.middleware.rate_limit import limiter
import inspect


def test_upload_endpoint_has_rate_limit():
    """
    Verify that the upload endpoint has rate limiting configured.
    """
    # Get the upload_audio_session function
    upload_func = sessions.upload_audio_session

    # Check if it has the limiter decorator by checking for the marker attribute
    # slowapi sets a _rate_limit_marker attribute on decorated functions
    assert hasattr(upload_func, '__wrapped__') or hasattr(upload_func, '_rate_limit_marker') or \
           any('limiter' in str(d) for d in getattr(upload_func, '__decorators__', [])), \
           "Upload endpoint should have rate limiting decorator"

    # Verify the function signature includes Request parameter (required for slowapi)
    sig = inspect.signature(upload_func)
    assert 'request' in sig.parameters, "Upload endpoint must have 'request' parameter for rate limiting"


def test_extract_notes_endpoint_has_rate_limit():
    """
    Verify that the extract-notes endpoint has rate limiting configured.
    """
    # Get the manually_extract_notes function
    extract_func = sessions.manually_extract_notes

    # Check if it has the limiter decorator
    assert hasattr(extract_func, '__wrapped__') or hasattr(extract_func, '_rate_limit_marker') or \
           any('limiter' in str(d) for d in getattr(extract_func, '__decorators__', [])), \
           "Extract notes endpoint should have rate limiting decorator"

    # Verify the function signature includes Request parameter
    sig = inspect.signature(extract_func)
    assert 'request' in sig.parameters, "Extract notes endpoint must have 'request' parameter for rate limiting"


def test_rate_limiter_configured():
    """
    Verify that the global rate limiter is properly configured.
    """
    # Check that limiter exists
    assert limiter is not None, "Rate limiter should be configured"

    # Check that limiter has default limits
    assert limiter._default_limits is not None, "Rate limiter should have default limits configured"
    assert len(limiter._default_limits) > 0, "Rate limiter should have at least one default limit"


def test_rate_limit_values():
    """
    Verify that rate limits are set to appropriate values.

    This is a documentation test to ensure the limits match the specification:
    - Upload: 10/hour
    - Extract notes: 20/hour
    """
    # Read the source code to verify the rate limit decorators
    import inspect

    # Check upload endpoint
    upload_source = inspect.getsource(sessions.upload_audio_session)
    assert '@limiter.limit("10/hour")' in upload_source, \
           "Upload endpoint should have 10/hour rate limit"

    # Check extract notes endpoint
    extract_source = inspect.getsource(sessions.manually_extract_notes)
    assert '@limiter.limit("20/hour")' in extract_source, \
           "Extract notes endpoint should have 20/hour rate limit"
