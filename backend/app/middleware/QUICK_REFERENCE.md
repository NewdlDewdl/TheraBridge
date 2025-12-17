# Exception Handling Quick Reference

## Import
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

## Common Patterns

### Audio Transcription
```python
raise TranscriptionError(
    message="Whisper API failed: timeout",
    retriable=True,
    details={"file": file_path}
)
```

### AI Note Extraction
```python
raise ExtractionError(
    message="OpenAI API error: rate limit",
    retriable=True
)
```

### Database Operations
```python
# Query failed
raise DatabaseError(
    message=f"Query failed: {str(e)}",
    retriable=True
)

# Resource not found
raise ResourceNotFoundError(
    resource_type="Session",
    resource_id=str(session_id)
)
```

### Validation
```python
raise ValidationError(
    message="Invalid file format",
    user_message="Only MP3, WAV, M4A files allowed",
    details={"file_format": file_ext}
)
```

### Authentication
```python
# Invalid token
raise AuthenticationError(
    message="JWT token expired",
    user_message="Your session expired. Please log in again."
)

# Insufficient permissions
raise AuthorizationError(
    message=f"User {user_id} lacks access",
    user_message="You don't have permission to access this resource."
)
```

## Exception Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | str | Yes | Internal error message (logged, not sent to client) |
| `user_message` | str | No | Client-safe message (displayed in frontend) |
| `retriable` | bool | No | Whether client should retry (default varies) |
| `details` | dict | No | Additional context (sanitized for client) |

## Error Response
```json
{
  "error": {
    "code": "TRANSCRIPTION_ERROR",
    "message": "Failed to transcribe audio file...",
    "retriable": true,
    "request_id": "uuid-here",
    "details": {}
  }
}
```

## When to Use Each Exception

| Exception | Use When... |
|-----------|-------------|
| `TranscriptionError` | Whisper API fails, audio processing errors |
| `ExtractionError` | OpenAI API fails, JSON parsing errors |
| `DatabaseError` | DB connection fails, query timeout |
| `ResourceNotFoundError` | Session/Patient/User doesn't exist |
| `ValidationError` | Invalid input data, constraint violation |
| `AuthenticationError` | Token invalid/expired, login fails |
| `AuthorizationError` | User lacks required permissions |

## Default Values

| Exception | Default HTTP Status | Default Retriable |
|-----------|---------------------|-------------------|
| `TranscriptionError` | 500 | Yes |
| `ExtractionError` | 500 | Yes |
| `DatabaseError` | 500 | Yes |
| `ResourceNotFoundError` | 404 | No |
| `ValidationError` | 422 | No |
| `AuthenticationError` | 401 | No |
| `AuthorizationError` | 403 | No |

## Full Documentation
- **Usage examples**: See `USAGE_EXAMPLES.md`
- **Implementation details**: See `ERROR_HANDLING_SUMMARY.md`
- **Test cases**: See `test_error_handler.py`
