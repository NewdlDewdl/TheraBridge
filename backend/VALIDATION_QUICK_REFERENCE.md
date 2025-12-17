# Input Validation Quick Reference

**For developers working on TherapyBridge API**

## Import the validators

```python
from app.validators import (
    validate_email,
    validate_phone,
    validate_required_string,
    validate_positive_int,
    sanitize_filename,
    validate_audio_file_header,
    validate_patient_exists,
    validate_therapist_exists,
    validate_session_exists
)
```

## Common Validation Patterns

### Validate Email (Optional Field)
```python
validated_email = validate_email(user_input.email, field_name="email")
# Returns None if email is None or empty
# Returns normalized email (lowercase) if valid
# Raises HTTPException 400 if invalid format
```

### Validate Phone (Optional Field)
```python
validated_phone = validate_phone(user_input.phone, field_name="phone")
# Returns None if phone is None or empty
# Returns normalized phone (digits only with optional +) if valid
# Raises HTTPException 400 if invalid format
```

### Validate Required String
```python
validated_name = validate_required_string(
    user_input.name,
    field_name="name",
    min_length=1,
    max_length=255
)
# Raises HTTPException 400 if empty, too short, or too long
```

### Validate Positive Integer with Bounds
```python
validated_limit = validate_positive_int(
    limit,
    field_name="limit",
    max_value=1000
)
# Raises HTTPException 400 if < 1 or > max_value
```

### Validate Patient/Therapist/Session Exists
```python
patient = await validate_patient_exists(patient_id, db)
# Returns Patient object if found
# Raises HTTPException 404 if not found

therapist = await validate_therapist_exists(therapist_id, db)
# Returns User object if found and role is "therapist"
# Raises HTTPException 404 if not found
# Raises HTTPException 400 if user is not a therapist

session = await validate_session_exists(session_id, db)
# Returns Session object if found
# Raises HTTPException 404 if not found
```

### Sanitize Uploaded Filename
```python
safe_filename = sanitize_filename(uploaded_file.filename)
# Removes dangerous characters
# Prevents path traversal
# Blocks reserved system names
# Raises HTTPException 400 if filename is dangerous
```

### Validate Audio File Header (Magic Bytes)
```python
detected_mime_type = validate_audio_file_header(file_path)
# Reads first 12 bytes and checks against known audio signatures
# Returns detected MIME type (e.g., "audio/mpeg", "audio/wav")
# Raises HTTPException 415 if file doesn't match audio formats
# Use AFTER file upload completes, BEFORE processing
```

## Endpoint Validation Checklist

When creating a new endpoint, validate:

- [ ] **Required strings:** Use `validate_required_string()`
- [ ] **Email fields:** Use `validate_email()` (returns None for optional)
- [ ] **Phone fields:** Use `validate_phone()` (returns None for optional)
- [ ] **Integer parameters:** Use `validate_positive_int()` with max_value
- [ ] **UUID foreign keys:** Use `validate_*_exists()` functions
- [ ] **Uploaded filenames:** Use `sanitize_filename()`
- [ ] **Uploaded files:** Use `validate_audio_file_header()` after upload

## Error Handling

All validators raise `HTTPException` with descriptive messages:

```python
try:
    validated_email = validate_email(email)
except HTTPException as e:
    # e.status_code = 400, 404, 413, or 415
    # e.detail = "Invalid email format: 'bad-email'. Expected format: user@example.com"
    pass  # FastAPI automatically returns error response
```

You don't need to catch these exceptions - FastAPI handles them automatically.

## Example: Complete Endpoint Validation

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.validators import (
    validate_email,
    validate_phone,
    validate_required_string,
    validate_therapist_exists
)

@router.post("/patients", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new patient.

    Validation:
        - Name is required (1-255 chars)
        - Email must be valid RFC 5322 format
        - Phone must be valid E.164 or common format
        - Therapist ID must exist and be a therapist
    """
    # Validate all inputs
    validated_name = validate_required_string(
        patient.name,
        field_name="name",
        min_length=1,
        max_length=255
    )

    validated_email = validate_email(patient.email)
    validated_phone = validate_phone(patient.phone)

    therapist = await validate_therapist_exists(patient.therapist_id, db)

    # Create with validated data
    new_patient = db_models.Patient(
        name=validated_name,
        email=validated_email,
        phone=validated_phone,
        therapist_id=therapist.id
    )

    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    return PatientResponse.model_validate(new_patient)
```

## File Upload Validation Pattern

```python
@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file with comprehensive validation."""

    # 1. Sanitize filename
    safe_filename = sanitize_filename(file.filename)

    # 2. Save file (with size checks)
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}{Path(safe_filename).suffix}"
    with open(file_path, "wb") as buffer:
        # Stream and write file...
        pass

    # 3. Validate file header AFTER upload
    try:
        detected_mime = validate_audio_file_header(file_path)
        logger.info(f"File validated: {detected_mime}")
    except HTTPException:
        # Validation failed - delete file
        file_path.unlink(missing_ok=True)
        raise

    # 4. Process file
    # ...
```

## Common Pitfalls

### ❌ DON'T: Skip validation for "optional" fields
```python
# BAD - allows invalid emails to be stored
new_patient = Patient(email=patient.email)
```

### ✅ DO: Validate optional fields (returns None if empty)
```python
# GOOD - validates format or returns None
validated_email = validate_email(patient.email)
new_patient = Patient(email=validated_email)
```

### ❌ DON'T: Trust filename or MIME type alone
```python
# BAD - attacker can rename malware.exe to audio.mp3
if file.filename.endswith(".mp3"):
    process_audio(file)
```

### ✅ DO: Validate file headers (magic bytes)
```python
# GOOD - checks actual file contents
detected_mime = validate_audio_file_header(file_path)
if detected_mime == "audio/mpeg":
    process_audio(file)
```

### ❌ DON'T: Create records with unvalidated foreign keys
```python
# BAD - creates orphaned record if patient doesn't exist
session = Session(patient_id=patient_id)
db.add(session)
```

### ✅ DO: Validate foreign key existence first
```python
# GOOD - ensures patient exists before creating session
patient = await validate_patient_exists(patient_id, db)
session = Session(patient_id=patient.id)
db.add(session)
```

## Testing Your Validation

```python
import pytest
from fastapi import HTTPException

def test_validates_invalid_input(client):
    """Test that invalid input is rejected."""
    response = client.post("/patients", json={
        "name": "",  # Invalid: empty
        "email": "not-an-email",  # Invalid: bad format
        "phone": "123",  # Invalid: too short
        "therapist_id": "00000000-0000-0000-0000-000000000000"  # Invalid: doesn't exist
    })
    assert response.status_code in [400, 404]
    assert "detail" in response.json()

def test_validates_valid_input(client, therapist_id):
    """Test that valid input is accepted."""
    response = client.post("/patients", json={
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "therapist_id": str(therapist_id)
    })
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"  # Normalized
```

## Performance Considerations

- **Email/Phone regex:** ~0.01ms (compiled once)
- **Magic bytes read:** ~0.1ms (only 12 bytes)
- **UUID DB lookup:** ~10ms (required for integrity)

**Total overhead:** < 50ms per request

This is negligible compared to the security and data integrity benefits.

## Questions?

See full documentation in:
- `/backend/app/validators.py` - Function implementations with docstrings
- `/backend/VALIDATION_IMPLEMENTATION.md` - Detailed implementation guide
- `/backend/VALIDATION_SUMMARY.md` - Complete feature summary
