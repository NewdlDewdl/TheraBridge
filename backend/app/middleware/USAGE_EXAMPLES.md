# Exception Handling Usage Examples

## Quick Reference

Import exceptions from middleware:
```python
from app.middleware import (
    TranscriptionError,
    ExtractionError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)
```

## Usage in Services

### 1. Transcription Service
```python
from app.middleware import TranscriptionError

async def transcribe_audio(file_path: str):
    try:
        # Attempt transcription
        result = await whisper_client.transcribe(file_path)
        return result
    except Exception as e:
        raise TranscriptionError(
            message=f"Whisper API failed: {str(e)}",
            user_message="Failed to transcribe audio. Please ensure the file is a valid audio format.",
            retriable=True,
            details={"file_path": file_path}
        )
```

### 2. Extraction Service
```python
from app.middleware import ExtractionError

async def extract_notes(transcript: str):
    try:
        # Call OpenAI API
        response = await openai_client.complete(transcript)
        return response
    except OpenAIError as e:
        raise ExtractionError(
            message=f"OpenAI API error: {str(e)}",
            user_message="Failed to extract therapy notes. Please try again.",
            retriable=True
        )
    except json.JSONDecodeError as e:
        raise ExtractionError(
            message=f"Failed to parse AI response: {str(e)}",
            user_message="Received invalid response from AI service.",
            retriable=True
        )
```

### 3. Database Operations
```python
from app.middleware import DatabaseError, ResourceNotFoundError
from sqlalchemy.exc import IntegrityError

async def get_session(session_id: int):
    try:
        session = await db.get(Session, session_id)
        if not session:
            raise ResourceNotFoundError(
                resource_type="Session",
                resource_id=str(session_id)
            )
        return session
    except Exception as e:
        raise DatabaseError(
            message=f"Failed to fetch session {session_id}: {str(e)}",
            retriable=True
        )

async def create_session(data: dict):
    try:
        session = Session(**data)
        await db.add(session)
        await db.commit()
        return session
    except IntegrityError as e:
        raise DatabaseError(
            message=f"Database constraint violation: {str(e)}",
            user_message="Failed to create session due to data conflict.",
            retriable=False
        )
```

### 4. Validation
```python
from app.middleware import ValidationError

def validate_audio_file(file):
    """Validate uploaded audio file"""
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac']

    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            message=f"File size {file.size} exceeds maximum {MAX_FILE_SIZE}",
            user_message="File is too large. Maximum size is 100MB.",
            details={"file_size": file.size, "max_size": MAX_FILE_SIZE}
        )

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FORMATS:
        raise ValidationError(
            message=f"Invalid file format: {file_ext}",
            user_message=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_FORMATS)}",
            details={"file_format": file_ext, "allowed_formats": ALLOWED_FORMATS}
        )
```

### 5. Authentication & Authorization
```python
from app.middleware import AuthenticationError, AuthorizationError

async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(
            message="JWT token expired",
            user_message="Your session has expired. Please log in again."
        )
    except jwt.InvalidTokenError:
        raise AuthenticationError(
            message="Invalid JWT token",
            user_message="Invalid authentication token."
        )

async def check_permission(user_id: int, resource_id: int):
    if not await user_has_access(user_id, resource_id):
        raise AuthorizationError(
            message=f"User {user_id} lacks access to resource {resource_id}",
            user_message="You do not have permission to access this resource.",
            details={"user_id": user_id, "resource_id": resource_id}
        )
```

## Error Response Format

All exceptions return consistent JSON structure:
```json
{
  "error": {
    "code": "TRANSCRIPTION_ERROR",
    "message": "Failed to transcribe audio file. Please ensure the file is a valid audio format and try again.",
    "retriable": true,
    "request_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
    "details": {
      "file_path": "/uploads/session_123.mp3"
    }
  }
}
```

## Benefits

1. **Consistent Error Format**: All errors follow same structure
2. **Request Tracing**: Every error includes unique request_id
3. **User-Friendly Messages**: Safe messages for frontend display
4. **Retriable Flags**: Client knows when to retry
5. **Secure Logging**: Internal details logged but not exposed to clients
6. **Type Safety**: IDE autocomplete for exception types
7. **Centralized Handling**: No need to write error handling in every endpoint
