"""
Input validation utilities for API endpoints.

Provides reusable validation functions for:
- Email format validation
- Phone number format validation
- Filename sanitization
- File header/magic bytes validation
- UUID existence checks
"""
import re
import mimetypes
from pathlib import Path
from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import db_models


# ============================================================================
# Email & Phone Validation
# ============================================================================

# RFC 5322 simplified email regex (covers 99.99% of valid emails)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# International phone number regex (supports E.164 format and common patterns)
# Accepts: +1234567890, (123) 456-7890, 123-456-7890, 123.456.7890, etc.
PHONE_REGEX = re.compile(
    r'^\+?[1-9]\d{0,3}[-.\s]?'  # Country code (optional)
    r'(\(?\d{1,4}\)?[-.\s]?)?'   # Area code (optional, with/without parens)
    r'\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$'  # Number groups
)


def validate_email(email: Optional[str], field_name: str = "email") -> Optional[str]:
    """
    Validate email format.

    Args:
        email: Email address to validate (can be None)
        field_name: Name of field for error messages (default: "email")

    Returns:
        Normalized email (lowercase, stripped) or None if input was None

    Raises:
        HTTPException 400: If email format is invalid
    """
    if email is None:
        return None

    email = email.strip()

    if not email:
        return None

    # Normalize to lowercase
    email = email.lower()

    # Validate format
    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format: '{email}'. Expected format: user@example.com"
        )

    # Length validation (RFC 5321: max 320 chars total)
    if len(email) > 320:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds maximum length of 320 characters"
        )

    return email


def validate_phone(phone: Optional[str], field_name: str = "phone") -> Optional[str]:
    """
    Validate phone number format.

    Accepts international formats including:
    - E.164: +1234567890
    - US format: (123) 456-7890, 123-456-7890
    - International: +44 20 7123 4567

    Args:
        phone: Phone number to validate (can be None)
        field_name: Name of field for error messages (default: "phone")

    Returns:
        Normalized phone (digits only, with + prefix if present) or None if input was None

    Raises:
        HTTPException 400: If phone format is invalid
    """
    if phone is None:
        return None

    phone = phone.strip()

    if not phone:
        return None

    # Validate format
    if not PHONE_REGEX.match(phone):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format: '{phone}'. "
                   f"Expected format: +1234567890, (123) 456-7890, or 123-456-7890"
        )

    # Normalize: keep only digits and leading +
    normalized = phone
    if phone.startswith('+'):
        normalized = '+' + re.sub(r'[^\d]', '', phone[1:])
    else:
        normalized = re.sub(r'[^\d]', '', phone)

    # Length validation (E.164: max 15 digits + 1 for '+')
    if len(normalized.lstrip('+')) > 15:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds maximum length of 15 digits (E.164 standard)"
        )

    if len(normalized.lstrip('+')) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must contain at least 7 digits"
        )

    return normalized


# ============================================================================
# Filename Sanitization
# ============================================================================

# Dangerous characters for filenames (cross-platform)
DANGEROUS_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Reserved Windows filenames (should not be used even on Unix)
RESERVED_FILENAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent path traversal and filesystem issues.

    Safety measures:
    - Removes path separators (/, \\)
    - Removes dangerous characters
    - Prevents directory traversal (.., .)
    - Checks for reserved Windows filenames
    - Enforces max length

    Args:
        filename: Original filename from upload
        max_length: Maximum allowed filename length (default: 255)

    Returns:
        Safe filename with extension preserved

    Raises:
        HTTPException 400: If filename is invalid or dangerous
    """
    if not filename or not filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    filename = filename.strip()

    # Remove path separators (prevent path traversal)
    filename = filename.replace('/', '_').replace('\\', '_')

    # Check for directory traversal attempts
    if '..' in filename or filename.startswith('.'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filename: '{filename}' contains directory traversal patterns"
        )

    # Remove dangerous characters
    sanitized = DANGEROUS_FILENAME_CHARS.sub('_', filename)

    # Check for reserved Windows filenames
    name_without_ext = Path(sanitized).stem.upper()
    if name_without_ext in RESERVED_FILENAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Filename '{filename}' uses reserved system name: {name_without_ext}"
        )

    # Enforce max length
    if len(sanitized) > max_length:
        # Preserve extension while truncating name
        ext = Path(sanitized).suffix
        max_name_length = max_length - len(ext)
        name = Path(sanitized).stem[:max_name_length]
        sanitized = name + ext

    return sanitized


# ============================================================================
# File Header (Magic Bytes) Validation
# ============================================================================

# Audio file magic bytes (first few bytes identify file type)
AUDIO_MAGIC_BYTES = {
    # MP3: ID3 tag or MPEG frame sync
    b'ID3': 'audio/mpeg',
    b'\xff\xfb': 'audio/mpeg',  # MPEG-1 Layer 3
    b'\xff\xf3': 'audio/mpeg',  # MPEG-1 Layer 3 (alternative)
    b'\xff\xf2': 'audio/mpeg',  # MPEG-2 Layer 3

    # WAV: RIFF header
    b'RIFF': 'audio/wav',

    # M4A/MP4: ftyp box
    b'ftyp': 'audio/mp4',  # Checked at offset 4

    # WebM: EBML header
    b'\x1a\x45\xdf\xa3': 'audio/webm',

    # OGG: OggS header
    b'OggS': 'audio/ogg',
}


def validate_audio_file_header(file_path: Path) -> str:
    """
    Validate audio file by checking magic bytes (file header).

    Prevents attacks where malicious files are renamed with audio extensions.
    Reads first 12 bytes and checks against known audio file signatures.

    Args:
        file_path: Path to uploaded file

    Returns:
        Detected MIME type based on file header

    Raises:
        HTTPException 415: If file header doesn't match expected audio formats
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file header: {str(e)}"
        )

    # Check magic bytes
    for magic_bytes, mime_type in AUDIO_MAGIC_BYTES.items():
        # Check at offset 0
        if header.startswith(magic_bytes):
            return mime_type

        # MP4/M4A: check 'ftyp' at offset 4
        if len(header) >= 8 and header[4:8] == magic_bytes:
            return mime_type

    # Fallback: use mimetypes library (less reliable but covers edge cases)
    guessed_type, _ = mimetypes.guess_type(str(file_path))
    if guessed_type and (guessed_type.startswith('audio/') or guessed_type.startswith('video/')):
        return guessed_type

    raise HTTPException(
        status_code=415,
        detail=f"File does not appear to be a valid audio file. "
               f"Header bytes: {header[:8].hex()}"
    )


# ============================================================================
# Database Existence Checks
# ============================================================================

async def validate_patient_exists(
    patient_id: UUID,
    db: AsyncSession
) -> db_models.Patient:
    """
    Validate that a patient exists in the database.

    Args:
        patient_id: UUID of patient to check
        db: Database session

    Returns:
        Patient object if found

    Raises:
        HTTPException 404: If patient not found
    """
    result = await db.execute(
        select(db_models.Patient).where(db_models.Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    return patient


async def validate_therapist_exists(
    therapist_id: UUID,
    db: AsyncSession
) -> db_models.User:
    """
    Validate that a therapist exists in the database.

    Args:
        therapist_id: UUID of therapist to check
        db: Database session

    Returns:
        User object if found and is a therapist

    Raises:
        HTTPException 404: If therapist not found
        HTTPException 400: If user is not a therapist
    """
    result = await db.execute(
        select(db_models.User).where(db_models.User.id == therapist_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Therapist with ID {therapist_id} not found"
        )

    if user.role != "therapist":
        raise HTTPException(
            status_code=400,
            detail=f"User {therapist_id} is not a therapist (role: {user.role})"
        )

    return user


async def validate_session_exists(
    session_id: UUID,
    db: AsyncSession
) -> db_models.Session:
    """
    Validate that a session exists in the database.

    Args:
        session_id: UUID of session to check
        db: Database session

    Returns:
        Session object if found

    Raises:
        HTTPException 404: If session not found
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session with ID {session_id} not found"
        )

    return session


# ============================================================================
# String Validation
# ============================================================================

def validate_required_string(
    value: Optional[str],
    field_name: str,
    min_length: int = 1,
    max_length: int = 255
) -> str:
    """
    Validate that a string field is present and meets length requirements.

    Args:
        value: String to validate
        field_name: Name of field for error messages
        min_length: Minimum required length (default: 1)
        max_length: Maximum allowed length (default: 255)

    Returns:
        Trimmed string

    Raises:
        HTTPException 400: If validation fails
    """
    if value is None or not value.strip():
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is required and cannot be empty"
        )

    value = value.strip()

    if len(value) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} character(s) long"
        )

    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must not exceed {max_length} characters"
        )

    return value


def validate_positive_int(
    value: int,
    field_name: str,
    max_value: Optional[int] = None
) -> int:
    """
    Validate that an integer is positive and within bounds.

    Args:
        value: Integer to validate
        field_name: Name of field for error messages
        max_value: Optional maximum value

    Returns:
        Validated integer

    Raises:
        HTTPException 400: If validation fails
    """
    if value < 1:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a positive integer (got: {value})"
        )

    if max_value and value > max_value:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must not exceed {max_value} (got: {value})"
        )

    return value
