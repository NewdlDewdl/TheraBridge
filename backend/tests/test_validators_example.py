"""
Example unit tests for input validation utilities.

These tests demonstrate how to test the validators in app/validators.py.
Run with: pytest tests/test_validators_example.py -v
"""
import pytest
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException

from app.validators import (
    validate_email,
    validate_phone,
    validate_required_string,
    validate_positive_int,
    sanitize_filename,
    validate_audio_file_header,
)


# ============================================================================
# Email Validation Tests
# ============================================================================

def test_validate_email_valid():
    """Valid email addresses should be accepted and normalized."""
    assert validate_email("user@example.com") == "user@example.com"
    assert validate_email("USER@EXAMPLE.COM") == "user@example.com"  # Normalized to lowercase
    assert validate_email("  user@example.com  ") == "user@example.com"  # Trimmed
    assert validate_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"


def test_validate_email_optional():
    """None or empty email should return None (optional field)."""
    assert validate_email(None) is None
    assert validate_email("") is None
    assert validate_email("   ") is None


def test_validate_email_invalid():
    """Invalid email formats should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_email("not-an-email")
    assert exc.value.status_code == 400
    assert "Invalid email format" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_email("@example.com")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        validate_email("user@")
    assert exc.value.status_code == 400


def test_validate_email_too_long():
    """Email exceeding 320 characters should be rejected."""
    long_email = "a" * 310 + "@example.com"  # 324 chars
    with pytest.raises(HTTPException) as exc:
        validate_email(long_email)
    assert exc.value.status_code == 400
    assert "maximum length" in exc.value.detail


# ============================================================================
# Phone Validation Tests
# ============================================================================

def test_validate_phone_valid():
    """Valid phone numbers should be accepted and normalized."""
    assert validate_phone("+1234567890") == "+1234567890"
    assert validate_phone("(123) 456-7890") == "1234567890"  # Normalized to digits
    assert validate_phone("123-456-7890") == "1234567890"
    assert validate_phone("+44 20 7123 4567") == "+442071234567"
    assert validate_phone("123.456.7890") == "1234567890"


def test_validate_phone_optional():
    """None or empty phone should return None (optional field)."""
    assert validate_phone(None) is None
    assert validate_phone("") is None
    assert validate_phone("   ") is None


def test_validate_phone_invalid():
    """Invalid phone formats should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_phone("123")  # Too short
    assert exc.value.status_code == 400
    assert "must contain at least 7 digits" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_phone("not-a-phone")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        validate_phone("12345678901234567890")  # Too long (>15 digits)
    assert exc.value.status_code == 400
    assert "maximum length" in exc.value.detail


# ============================================================================
# String Validation Tests
# ============================================================================

def test_validate_required_string_valid():
    """Valid strings should be accepted and trimmed."""
    assert validate_required_string("hello", "name") == "hello"
    assert validate_required_string("  hello  ", "name") == "hello"
    assert validate_required_string("a" * 255, "name", max_length=255) == "a" * 255


def test_validate_required_string_empty():
    """Empty or whitespace-only strings should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_required_string("", "name")
    assert exc.value.status_code == 400
    assert "is required" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_required_string("   ", "name")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        validate_required_string(None, "name")
    assert exc.value.status_code == 400


def test_validate_required_string_too_short():
    """Strings below min_length should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_required_string("ab", "username", min_length=3)
    assert exc.value.status_code == 400
    assert "at least 3 character(s)" in exc.value.detail


def test_validate_required_string_too_long():
    """Strings exceeding max_length should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_required_string("a" * 256, "name", max_length=255)
    assert exc.value.status_code == 400
    assert "must not exceed 255 characters" in exc.value.detail


# ============================================================================
# Integer Validation Tests
# ============================================================================

def test_validate_positive_int_valid():
    """Positive integers within bounds should be accepted."""
    assert validate_positive_int(1, "limit") == 1
    assert validate_positive_int(100, "limit") == 100
    assert validate_positive_int(1000, "limit", max_value=1000) == 1000


def test_validate_positive_int_negative():
    """Zero or negative integers should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_positive_int(0, "limit")
    assert exc.value.status_code == 400
    assert "must be a positive integer" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_positive_int(-5, "limit")
    assert exc.value.status_code == 400


def test_validate_positive_int_exceeds_max():
    """Integers exceeding max_value should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        validate_positive_int(1001, "limit", max_value=1000)
    assert exc.value.status_code == 400
    assert "must not exceed 1000" in exc.value.detail


# ============================================================================
# Filename Sanitization Tests
# ============================================================================

def test_sanitize_filename_valid():
    """Valid filenames should pass through unchanged."""
    assert sanitize_filename("test.mp3") == "test.mp3"
    assert sanitize_filename("my file.wav") == "my file.wav"
    assert sanitize_filename("audio_2024.m4a") == "audio_2024.m4a"


def test_sanitize_filename_dangerous_chars():
    """Dangerous characters should be replaced with underscores."""
    assert sanitize_filename("file<>|?.mp3") == "file_____.mp3"
    assert sanitize_filename('file:name"test.mp3') == "file_name_test.mp3"


def test_sanitize_filename_path_traversal():
    """Path traversal attempts should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        sanitize_filename("../../etc/passwd.mp3")
    assert exc.value.status_code == 400
    assert "directory traversal" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        sanitize_filename(".hidden.mp3")  # Starts with .
    assert exc.value.status_code == 400


def test_sanitize_filename_reserved_names():
    """Reserved Windows filenames should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        sanitize_filename("CON.mp3")
    assert exc.value.status_code == 400
    assert "reserved system name" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        sanitize_filename("PRN.wav")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        sanitize_filename("AUX.m4a")
    assert exc.value.status_code == 400


def test_sanitize_filename_too_long():
    """Filenames exceeding max_length should be truncated."""
    long_name = "a" * 300 + ".mp3"
    result = sanitize_filename(long_name, max_length=255)
    assert len(result) == 255
    assert result.endswith(".mp3")  # Extension preserved


def test_sanitize_filename_empty():
    """Empty filenames should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        sanitize_filename("")
    assert exc.value.status_code == 400
    assert "cannot be empty" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        sanitize_filename("   ")
    assert exc.value.status_code == 400


# ============================================================================
# File Header Validation Tests
# ============================================================================

@pytest.mark.skip(reason="Requires test audio files - implement when test files are available")
def test_validate_audio_file_header_mp3(tmp_path):
    """MP3 files should be detected by ID3 tag or MPEG frame sync."""
    # Create a test MP3 file with ID3 header
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"ID3" + b"\x00" * 100)  # ID3 header

    mime_type = validate_audio_file_header(mp3_file)
    assert mime_type == "audio/mpeg"


@pytest.mark.skip(reason="Requires test audio files - implement when test files are available")
def test_validate_audio_file_header_wav(tmp_path):
    """WAV files should be detected by RIFF header."""
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 100)  # RIFF header

    mime_type = validate_audio_file_header(wav_file)
    assert mime_type == "audio/wav"


@pytest.mark.skip(reason="Requires test audio files - implement when test files are available")
def test_validate_audio_file_header_m4a(tmp_path):
    """M4A files should be detected by ftyp box at offset 4."""
    m4a_file = tmp_path / "test.m4a"
    m4a_file.write_bytes(b"\x00\x00\x00\x00ftyp" + b"\x00" * 100)  # ftyp at offset 4

    mime_type = validate_audio_file_header(m4a_file)
    assert mime_type == "audio/mp4"


@pytest.mark.skip(reason="Requires test files - implement when test files are available")
def test_validate_audio_file_header_malicious(tmp_path):
    """Non-audio files should raise HTTPException 415."""
    # Create a fake MP3 that's actually an executable
    fake_mp3 = tmp_path / "malware.exe.mp3"
    fake_mp3.write_bytes(b"MZ\x90\x00" + b"\x00" * 100)  # PE executable header

    with pytest.raises(HTTPException) as exc:
        validate_audio_file_header(fake_mp3)
    assert exc.value.status_code == 415
    assert "does not appear to be a valid audio file" in exc.value.detail


# ============================================================================
# Database Validation Tests (require database fixture)
# ============================================================================

@pytest.mark.skip(reason="Requires database fixture - implement in integration tests")
@pytest.mark.asyncio
async def test_validate_patient_exists_valid(db_session, sample_patient):
    """Existing patient should be returned."""
    from app.validators import validate_patient_exists

    patient = await validate_patient_exists(sample_patient.id, db_session)
    assert patient.id == sample_patient.id
    assert patient.name == sample_patient.name


@pytest.mark.skip(reason="Requires database fixture - implement in integration tests")
@pytest.mark.asyncio
async def test_validate_patient_exists_invalid(db_session):
    """Non-existent patient should raise HTTPException 404."""
    from app.validators import validate_patient_exists

    fake_id = uuid4()
    with pytest.raises(HTTPException) as exc:
        await validate_patient_exists(fake_id, db_session)
    assert exc.value.status_code == 404
    assert "Patient" in exc.value.detail


@pytest.mark.skip(reason="Requires database fixture - implement in integration tests")
@pytest.mark.asyncio
async def test_validate_therapist_exists_valid(db_session, sample_therapist):
    """Existing therapist should be returned."""
    from app.validators import validate_therapist_exists

    therapist = await validate_therapist_exists(sample_therapist.id, db_session)
    assert therapist.id == sample_therapist.id
    assert therapist.role == "therapist"


@pytest.mark.skip(reason="Requires database fixture - implement in integration tests")
@pytest.mark.asyncio
async def test_validate_therapist_exists_wrong_role(db_session, sample_patient_user):
    """User with wrong role should raise HTTPException 400."""
    from app.validators import validate_therapist_exists

    with pytest.raises(HTTPException) as exc:
        await validate_therapist_exists(sample_patient_user.id, db_session)
    assert exc.value.status_code == 400
    assert "not a therapist" in exc.value.detail


# ============================================================================
# Notes for Implementation
# ============================================================================

"""
To complete these tests, you need:

1. Database fixtures (db_session, sample_patient, sample_therapist):
   - Set up test database with SQLite or PostgreSQL
   - Create fixtures in conftest.py
   - See FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/

2. Test audio files:
   - Create small test files with correct headers
   - Store in tests/fixtures/ directory
   - Or use bytes directly in tests (like in skipped examples above)

3. Async test support:
   - Install pytest-asyncio: pip install pytest-asyncio
   - Use @pytest.mark.asyncio decorator for async tests

Example conftest.py:
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.fixture
async def sample_patient(db_session):
    from app.models.db_models import Patient
    patient = Patient(name="Test Patient", email="test@example.com")
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient
```

Run tests:
    pytest tests/test_validators_example.py -v
    pytest tests/test_validators_example.py -v -k "email"  # Only email tests
    pytest tests/test_validators_example.py -v --cov=app.validators  # With coverage
"""
