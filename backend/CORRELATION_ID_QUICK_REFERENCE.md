# Correlation ID Quick Reference

## TL;DR

Every HTTP request now has a unique ID that flows through all logs. This enables end-to-end request tracing.

## Basic Usage

### Backend - Get Request ID

```python
from app.middleware.correlation_id import get_request_id

request_id = get_request_id()  # Returns UUID string
```

### Backend - Logging (Automatic)

```python
from app.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Processing request")  # request_id included automatically
```

### Frontend - Send Request ID

```typescript
const requestId = crypto.randomUUID();

fetch('/api/sessions', {
  headers: { 'X-Request-ID': requestId }
});
```

### Frontend - Read Request ID

```typescript
const response = await fetch('/api/sessions');
const requestId = response.headers.get('X-Request-ID');
```

## Configuration

### Enable JSON Logging (Production)

```bash
# .env
JSON_LOGS=true
LOG_LEVEL=INFO
```

## Testing

### Unit Tests
```bash
pytest tests/test_correlation_id.py -v
```

### Integration Test
```bash
# Terminal 1:
uvicorn app.main:app --reload

# Terminal 2:
python test_correlation_integration.py
```

### Manual Test
```bash
curl -i http://localhost:8000/
# Check for: X-Request-ID: <uuid>
```

## Log Example

```json
{
  "timestamp": "2025-12-17T10:30:15.123",
  "level": "INFO",
  "message": "Processing request",
  "request_id": "abc-123",
  "module": "sessions"
}
```

## Common Patterns

### Error Handling
```python
request_id = get_request_id()
raise HTTPException(
    status_code=500,
    detail=f"Error (request_id: {request_id})"
)
```

### External API Calls
```python
headers = {"X-Request-ID": get_request_id()}
response = await httpx.post(url, headers=headers)
```

### Background Tasks
```python
# Capture before task starts
request_id = get_request_id()
background_tasks.add_task(process, request_id=request_id)
```

## Files

- **Middleware:** `app/middleware/correlation_id.py`
- **Tests:** `tests/test_correlation_id.py`
- **Examples:** `correlation_id_example.py`
- **Full Guide:** `CORRELATION_ID_GUIDE.md`
- **Implementation:** `CORRELATION_ID_IMPLEMENTATION.md`

## Benefits

✅ Trace requests end-to-end
✅ Correlate logs across services
✅ Debug production issues faster
✅ Frontend-backend error correlation
✅ Works automatically - no code changes needed

## Support

- All logs automatically include `request_id` when `JSON_LOGS=true`
- Accepts `X-Request-ID`, `X-Correlation-ID`, `X-Trace-ID` headers
- Generates UUID v4 if no ID provided
- Thread-safe using contextvars
- Production-ready
