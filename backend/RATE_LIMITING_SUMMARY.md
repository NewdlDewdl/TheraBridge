# Rate Limiting Implementation Summary

## Overview
Rate limiting has been implemented on extraction endpoints to prevent OpenAI API quota exhaustion and protect against abuse.

## Implementation Details

### Endpoints Protected

1. **POST /api/sessions/upload** - Audio upload and processing
   - **Rate Limit:** 10 requests per hour per IP
   - **Reason:** Upload triggers transcription + note extraction (expensive API calls)
   - **Response:** 429 Too Many Requests with retry_after header

2. **POST /api/sessions/{session_id}/extract-notes** - Manual note extraction
   - **Rate Limit:** 20 requests per hour per IP
   - **Reason:** Direct OpenAI API call for note extraction
   - **Response:** 429 Too Many Requests with retry_after header

### Technology Stack

- **Library:** slowapi (v0.1.9)
- **Strategy:** Per-IP rate limiting using `get_remote_address`
- **Storage:** In-memory (suitable for single-instance deployments)
- **Global Default:** 100 requests per minute (for all other endpoints)

### Configuration

Rate limiter is configured in `/backend/app/middleware/rate_limit.py`:

```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)
```

Custom handler provides structured error responses:

```python
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests. Please try again later.",
    "retry_after": 3600  # seconds until rate limit resets
}
```

### Integration

1. **Main app setup** (`app/main.py`):
   ```python
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
   ```

2. **Endpoint decoration** (`app/routers/sessions.py`):
   ```python
   @router.post("/upload")
   @limiter.limit("10/hour")
   async def upload_audio_session(request: Request, ...):
       ...
   ```

## Testing

### Automated Tests
Location: `/backend/tests/test_rate_limiting.py`

Tests verify:
- ✅ Rate limiting decorators are applied
- ✅ Request parameter is included (required by slowapi)
- ✅ Correct rate limit values (10/hour, 20/hour)
- ✅ Global limiter is configured

Run tests:
```bash
cd backend
source venv/bin/activate
pytest tests/test_rate_limiting.py -v
```

### Manual Testing
Location: `/backend/tests/manual_rate_limit_test.py`

Interactive script to test rate limiting against live backend:
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Run test
python tests/manual_rate_limit_test.py
```

## Production Considerations

### Current Setup (Single Instance)
- In-memory storage is sufficient
- Rate limits reset on server restart
- Per-IP tracking works correctly

### Future Scaling (Multiple Instances)
If deploying multiple backend instances, consider:

1. **Redis-backed rate limiting:**
   ```python
   limiter = Limiter(
       key_func=get_remote_address,
       storage_uri="redis://localhost:6379"
   )
   ```

2. **API Gateway rate limiting:**
   - AWS API Gateway
   - Kong
   - Nginx rate limiting

### Customization

To adjust rate limits, edit the decorator in `app/routers/sessions.py`:

```python
# More restrictive
@limiter.limit("5/hour")

# More permissive
@limiter.limit("20/hour")

# Multiple time windows
@limiter.limit("10/hour;3/minute")
```

## Monitoring

### Metrics to Track
- Rate limit hit rate (429 responses)
- Average requests per user/IP
- API quota usage correlation

### Logging
Rate limit events are logged with correlation IDs for debugging.

### Alerts
Consider alerting on:
- High rate of 429 responses (potential attack)
- Low rate limits causing legitimate user issues

## Security Notes

- Rate limits are per-IP, not per-user (authentication not required)
- Proxies may share IP addresses (adjust limits accordingly)
- X-Forwarded-For header is trusted (ensure proper proxy configuration)
- No rate limit bypass mechanism (admin endpoints should use separate limits)

## References

- slowapi documentation: https://github.com/laurentS/slowapi
- FastAPI rate limiting: https://fastapi.tiangolo.com/advanced/middleware/
- Redis storage: https://slowapi.readthedocs.io/en/latest/#using-redis
