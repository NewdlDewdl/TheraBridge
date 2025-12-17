# Correlation ID Tracking Guide

## Overview

Request correlation IDs enable distributed tracing by providing a unique identifier for each HTTP request that flows through the entire system. This allows you to:

- Trace a single request across multiple services and logs
- Correlate all log entries for a specific request
- Debug issues by following the request journey
- Monitor request flows in production

## How It Works

### 1. Request Flow

```
Client Request → CorrelationIdMiddleware → Endpoint → Response
     ↓                      ↓                  ↓          ↓
X-Request-ID      Generate/Accept UUID    Log with ID   Add to Headers
```

### 2. Middleware Behavior

The `CorrelationIdMiddleware` (in `app/middleware/correlation_id.py`):

1. **Accepts client-provided request IDs** via headers:
   - `X-Request-ID` (primary)
   - `X-Correlation-ID` (alternative)
   - `X-Trace-ID` (alternative)

2. **Generates UUID** if no request ID provided

3. **Stores in context variable** (`request_id_context`) - accessible throughout request

4. **Adds to response headers** as `X-Request-ID`

5. **Automatically included in logs** via `JSONFormatter`

## Usage

### For Frontend/Client Developers

#### Sending Request IDs

```typescript
// TypeScript/JavaScript
const requestId = crypto.randomUUID();

fetch('http://localhost:8000/api/sessions', {
  headers: {
    'X-Request-ID': requestId
  }
});
```

```python
# Python
import uuid
import requests

request_id = str(uuid.uuid4())
requests.get(
    'http://localhost:8000/api/sessions',
    headers={'X-Request-ID': request_id}
)
```

#### Reading Response Request IDs

```typescript
const response = await fetch('/api/sessions');
const requestId = response.headers.get('X-Request-ID');
console.log('Request ID:', requestId);
```

### For Backend Developers

#### Accessing Request ID in Code

```python
from app.middleware.correlation_id import get_request_id

# In any endpoint, service, or function:
request_id = get_request_id()
logger.info("Processing request", extra={"request_id": request_id})
```

**Note**: The request ID is automatically included in logs when using JSON formatting, so you don't need to manually add it in most cases.

#### Logging with Request Context

```python
from app.logging_config import get_logger
from app.middleware.correlation_id import get_request_id

logger = get_logger(__name__)

@router.post("/sessions/upload")
async def upload_session(file: UploadFile):
    # Request ID automatically included in all logs
    logger.info("Starting session upload", extra={
        "filename": file.filename,
        "file_size": file.size
    })

    try:
        # ... processing logic ...
        logger.info("Upload successful", extra={"session_id": session_id})
    except Exception as e:
        logger.error("Upload failed", extra={"error": str(e)}, exc_info=True)

    # All logs above will include the same request_id
```

#### Example Log Output

**Human-readable format** (development):
```
2025-12-17 10:30:15 | INFO | app.routers.sessions | Starting session upload
2025-12-17 10:30:17 | INFO | app.services.transcription | Transcription started
2025-12-17 10:30:45 | INFO | app.services.note_extraction | Extracting notes
```

**JSON format** (production, with `JSON_LOGS=true`):
```json
{
  "timestamp": "2025-12-17T10:30:15.123456",
  "level": "INFO",
  "logger": "app.routers.sessions",
  "message": "Starting session upload",
  "module": "sessions",
  "function": "upload_session",
  "line": 125,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "session_recording.mp3",
  "file_size": 52428800
}
```

Notice the `request_id` field - this is the same across all logs for the request!

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Enable JSON logging (recommended for production)
JSON_LOGS=true

# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

### Frontend Configuration

CORS already configured to expose `X-Request-ID` header to frontend:

```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    expose_headers=["X-Request-ID"],  # ✅ Already configured
    # ...
)
```

## Testing

### Unit Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_correlation_id.py -v
```

### Integration Test

1. Start the backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

2. Run integration test:
```bash
python test_correlation_integration.py
```

### Manual Test with cURL

```bash
# Test auto-generation
curl -i http://localhost:8000/
# Look for X-Request-ID in response headers

# Test custom request ID
curl -i -H "X-Request-ID: test-123-abc" http://localhost:8000/
# Should return: X-Request-ID: test-123-abc

# Test alternative header
curl -i -H "X-Correlation-ID: test-456-def" http://localhost:8000/
# Should return: X-Request-ID: test-456-def
```

## Distributed Tracing Scenarios

### Scenario 1: Frontend → Backend

```typescript
// Frontend generates request ID
const requestId = crypto.randomUUID();

// Sends to backend
const response = await fetch('/api/sessions', {
  headers: { 'X-Request-ID': requestId }
});

// Backend logs include this request ID
// Frontend can correlate errors with backend logs
```

### Scenario 2: Backend → External Service

```python
from app.middleware.correlation_id import get_request_id

async def call_external_service():
    request_id = get_request_id()

    # Forward request ID to external service
    response = await httpx.post(
        'https://external-api.com/endpoint',
        headers={'X-Request-ID': request_id}
    )

    # Both backend and external service logs share same request ID
```

### Scenario 3: API Gateway → Multiple Microservices

```
API Gateway                Backend               Pipeline Service
    ↓                         ↓                        ↓
X-Request-ID: abc123  →  X-Request-ID: abc123  →  X-Request-ID: abc123
    ↓                         ↓                        ↓
All logs share the same request ID for end-to-end tracing
```

## Log Aggregation and Monitoring

### CloudWatch Insights Query

```sql
fields @timestamp, level, message, request_id, module
| filter request_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
| sort @timestamp asc
```

### Datadog Query

```
@request_id:"a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### ELK Stack Query

```json
{
  "query": {
    "match": {
      "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  }
}
```

## Best Practices

### ✅ DO

- **Always enable JSON logging in production** (`JSON_LOGS=true`)
- **Forward request IDs to external services** for full tracing
- **Use request IDs in error reports** to help debugging
- **Index request_id field** in log aggregation tools
- **Set short retention on request IDs** (they're just for tracing, not long-term storage)

### ❌ DON'T

- **Don't use request IDs as security tokens** (they're UUIDs, not secrets)
- **Don't store sensitive data in request IDs**
- **Don't rely on request IDs for authentication/authorization**
- **Don't manually set request IDs in production** (let middleware generate them)

## Troubleshooting

### Issue: Request ID not appearing in logs

**Solution**: Enable JSON logging:
```bash
# In .env
JSON_LOGS=true
```

Restart the server:
```bash
uvicorn app.main:app --reload
```

### Issue: Request ID changes between services

**Cause**: Not forwarding the header to downstream services.

**Solution**: Always include X-Request-ID when calling other services:
```python
headers = {'X-Request-ID': get_request_id()}
response = await httpx.post(url, headers=headers)
```

### Issue: Can't read X-Request-ID in frontend

**Cause**: CORS not exposing the header.

**Solution**: Already configured in `app/main.py`:
```python
expose_headers=["X-Request-ID"]
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         CorrelationIdMiddleware (FIRST)              │  │
│  │  - Accept/Generate Request ID                         │  │
│  │  - Store in context variable (request_id_context)     │  │
│  │  - Add to response headers                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Other Middleware (CORS, etc)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Endpoint Handlers                     │  │
│  │  - Access: get_request_id()                           │  │
│  │  - Logs automatically include request_id              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                JSONFormatter (Logging)                 │  │
│  │  - Automatically pulls request_id from context        │  │
│  │  - Includes in all log entries                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified/Created

### New Files
- `app/middleware/correlation_id.py` - Middleware implementation
- `tests/test_correlation_id.py` - Unit tests
- `test_correlation_integration.py` - Integration tests
- `CORRELATION_ID_GUIDE.md` - This documentation

### Modified Files
- `app/middleware/__init__.py` - Export correlation ID components
- `app/logging_config.py` - Auto-include request IDs in logs
- `app/main.py` - Register middleware

## Summary

The correlation ID system provides:

- ✅ **Automatic request ID generation** (UUID)
- ✅ **Client-provided request ID support** (X-Request-ID, X-Correlation-ID, X-Trace-ID)
- ✅ **Context variable storage** (thread-safe, request-scoped)
- ✅ **Automatic log inclusion** (via JSONFormatter)
- ✅ **Response header injection** (X-Request-ID)
- ✅ **CORS exposure** (frontend can read request IDs)
- ✅ **Production-ready** (tested, documented, configurable)

All requests now have traceable IDs that flow through logs, making debugging and monitoring significantly easier!
