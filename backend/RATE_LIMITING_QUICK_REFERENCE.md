# Rate Limiting Quick Reference

## Endpoints with Rate Limiting

### 1. Upload Endpoint
```
POST /api/sessions/upload
Rate Limit: 10 requests/hour per IP
```

**Why:** Each upload triggers:
- Audio transcription (OpenAI Whisper API)
- Note extraction (OpenAI GPT-4o API)
- Total cost: ~$0.50-2.00 per session

**Error Response (429):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 3600
}
```

### 2. Extract Notes Endpoint
```
POST /api/sessions/{session_id}/extract-notes
Rate Limit: 20 requests/hour per IP
```

**Why:** Direct OpenAI API call for re-processing (~$0.10-0.50 per call)

**Error Response (429):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 3600
}
```

## Implementation Summary

### Files Modified
1. `/backend/app/routers/sessions.py`
   - Added `Request` import
   - Added `limiter` import
   - Added `@limiter.limit("10/hour")` to upload endpoint
   - Added `@limiter.limit("20/hour")` to extract endpoint
   - Added `request: Request` parameter to both endpoints

### Files Created
1. `/backend/tests/test_rate_limiting.py` - Automated tests
2. `/backend/tests/manual_rate_limit_test.py` - Manual testing script
3. `/backend/RATE_LIMITING_SUMMARY.md` - Complete documentation

### Files Used (No Changes)
1. `/backend/app/middleware/rate_limit.py` - Rate limiter configuration
2. `/backend/app/main.py` - Rate limiter integration
3. `/backend/requirements.txt` - slowapi dependency (already present)

## Testing

### Run Automated Tests
```bash
cd backend
source venv/bin/activate
pytest tests/test_rate_limiting.py -v
```

**Expected Output:**
```
test_upload_endpoint_has_rate_limit PASSED
test_extract_notes_endpoint_has_rate_limit PASSED
test_rate_limiter_configured PASSED
test_rate_limit_values PASSED
```

### Run Manual Tests
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Run test script
python tests/manual_rate_limit_test.py
```

## How It Works

1. **Request arrives** → FastAPI receives request with IP address
2. **Limiter checks** → slowapi checks request count for this IP
3. **Within limit?**
   - ✅ YES → Process request normally
   - ❌ NO → Return 429 with retry_after header
4. **Counter updates** → Increment request count for this IP
5. **Reset timer** → Counter resets after 1 hour

## Configuration

### Current Settings
- **Storage:** In-memory (sufficient for single instance)
- **Key:** IP address (`get_remote_address`)
- **Default limit:** 100/minute (all other endpoints)
- **Upload limit:** 10/hour
- **Extract limit:** 20/hour

### Changing Limits

Edit `/backend/app/routers/sessions.py`:

```python
# More restrictive (5/hour instead of 10/hour)
@limiter.limit("5/hour")

# More permissive (30/hour instead of 10/hour)
@limiter.limit("30/hour")

# Multiple windows (10/hour AND max 3/minute)
@limiter.limit("10/hour;3/minute")
```

## Production Considerations

### Scaling to Multiple Instances
Current setup uses in-memory storage. For multiple backend instances:

**Option 1: Redis (Recommended)**
```python
# In app/middleware/rate_limit.py
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["100/minute"]
)
```

**Option 2: API Gateway**
- Use AWS API Gateway throttling
- Use Kong rate limiting plugin
- Use Nginx rate limiting module

### Monitoring
Track these metrics:
- Number of 429 responses (rate limit hits)
- Requests per IP distribution
- OpenAI API quota usage
- Cost per endpoint

### Alerts
Set up alerts for:
- High 429 rate (> 10% of requests)
- Single IP hitting limits repeatedly
- API quota approaching limit

## Cost Savings Estimate

**Without Rate Limiting:**
- Malicious actor: 1000 uploads/hour
- Cost: $500-2000/hour
- Monthly exposure: $360,000+

**With Rate Limiting (10/hour):**
- Max uploads: 10/hour per IP
- Cost per IP: $5-20/hour
- Even 100 IPs: $500-2000/hour (contained)
- Protection: Rate limiting + IP blocking

## Security Notes

⚠️ **Important:**
- Rate limits are per-IP, not per-user
- Shared IPs (offices, VPNs) share rate limits
- X-Forwarded-For header must be trusted (proxy config required)
- No admin bypass (by design)

## Troubleshooting

### Issue: Legitimate users hitting limits
**Solution:** Increase limits or use authentication-based rate limiting

### Issue: Rate limits not working
**Check:**
1. slowapi installed? `pip list | grep slowapi`
2. Limiter registered? Check `app.state.limiter` in main.py
3. Request parameter present? Check endpoint signature
4. Exception handler registered? Check main.py

### Issue: Rate limits reset on restart
**Expected:** In-memory storage resets on server restart
**Solution:** Use Redis for persistent storage

## References

- slowapi: https://github.com/laurentS/slowapi
- OpenAI Pricing: https://openai.com/pricing
- FastAPI Middleware: https://fastapi.tiangolo.com/advanced/middleware/
