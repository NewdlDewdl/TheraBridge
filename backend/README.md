# TherapyBridge Backend

FastAPI backend for therapy session management and AI note extraction.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

The backend uses the shared `.env` file from `audio-transcription-pipeline/`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# OpenAI
OPENAI_API_KEY=sk-xxx
```

### 3. Initialize Database

```bash
# Run migration (from backend directory)
python run_migration.py
```

### 4. Run Server

```bash
uvicorn app.main:app --reload
```

API will be available at http://localhost:8000

Interactive docs at http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── database.py          # DB connection
│   ├── models/
│   │   ├── schemas.py       # Pydantic models
│   │   └── db_models.py     # SQLAlchemy models
│   ├── routers/
│   │   ├── sessions.py      # Session endpoints
│   │   └── patients.py      # Patient endpoints
│   └── services/
│       ├── transcription.py # Audio transcription
│       └── note_extraction.py # AI extraction
├── tests/
│   ├── test_extraction_service.py
│   └── fixtures/
│       └── sample_transcripts.py
├── migrations/
│   └── 001_initial_schema.sql
└── requirements.txt
```

## API Endpoints

### Sessions
- `POST /api/sessions/upload` - Upload audio file
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/notes` - Get extracted notes
- `GET /api/sessions` - List all sessions
- `POST /api/sessions/{id}/extract-notes` - Manually trigger extraction

### Patients
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient details
- `GET /api/patients` - List all patients

### Health
- `GET /` - Simple health check
- `GET /health` - Detailed health status

## Testing

### Quick Test (Automated)
```bash
# Test the complete pipeline end-to-end
./test_pipeline.sh

# Or test with your own audio
./test_pipeline.sh /path/to/audio.mp3
```

### Unit Tests
```bash
# Run unit tests
pytest tests/test_extraction_service.py -v

# Run specific test
pytest tests/test_extraction_service.py::test_extract_notes_basic -v
```

### Comprehensive Testing
See detailed testing guides:
- **Quick start**: `TEST_PROMPT.md` - Simple testing steps
- **Full guide**: `TESTING_GUIDE.md` - Complete testing documentation with all edge cases
- **Quick reference**: `QUICKSTART.md` - Common operations

## Usage Example

### Upload Audio Session

```bash
curl -X POST http://localhost:8000/api/sessions/upload \
  -F "file=@session.mp3" \
  -F "patient_id=PATIENT_UUID"
```

### Check Session Status

```bash
curl http://localhost:8000/api/sessions/SESSION_ID
```

### Get Extracted Notes

```bash
curl http://localhost:8000/api/sessions/SESSION_ID/notes
```

## Processing Pipeline

1. **Upload** - Audio file saved, session created with status `uploading`
2. **Transcription** - Whisper API transcribes audio → status `transcribing`
3. **Extraction** - GPT-4o extracts structured notes → status `extracting_notes`
4. **Complete** - All data saved → status `processed`

Processing happens in background after upload returns immediately.

## Authentication

TherapyBridge uses JWT-based authentication with refresh token rotation for security.

### Endpoints

#### POST /api/auth/signup
Create a new user account and receive authentication tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password123",
  "full_name": "Dr. Jane Smith",
  "role": "therapist"  // or "patient" or "admin"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "a1b2c3...",
  "token_type": "bearer",
  "expires_in": 1800  // seconds (30 minutes)
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "therapist@example.com",
    "password": "securepass123",
    "full_name": "Dr. Test User",
    "role": "therapist"
  }'
```

#### POST /api/auth/login
Authenticate with existing credentials.

**Rate Limit:** 5 requests per minute per IP (prevents brute force attacks)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "a1b2c3...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "therapist@example.com",
    "password": "securepass123"
  }'
```

#### POST /api/auth/refresh
Get new access token using refresh token (with token rotation).

**Security:** Old refresh token is automatically revoked when used, preventing replay attacks.

**Request:**
```json
{
  "refresh_token": "a1b2c3..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "x9y8z7...",  // NEW refresh token
  "token_type": "bearer",
  "expires_in": 1800
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

#### POST /api/auth/logout
Revoke refresh token (logout).

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "a1b2c3..."
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

#### GET /api/auth/me
Get current authenticated user's information.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Dr. Jane Smith",
  "role": "therapist",
  "is_active": true,
  "created_at": "2025-12-17T10:30:00Z"
}
```

**curl Example:**
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Password Requirements

- **Minimum length:** 8 characters
- **Validation:** Enforced at API level via Pydantic schemas
- **Storage:** Bcrypt hashing with automatic salt generation
- **Cost factor:** 12 rounds (balanced security vs performance)

### Token Expiration

| Token Type | Duration | Purpose |
|------------|----------|---------|
| Access Token | 30 minutes | API authentication |
| Refresh Token | 7 days | Generate new access tokens |

**Best Practice:** Store refresh token securely (httpOnly cookie in production), keep access token in memory only.

### Rate Limits

| Endpoint | Limit | Window | Purpose |
|----------|-------|--------|---------|
| POST /api/auth/login | 5 requests | 1 minute | Prevent brute force |
| All other endpoints | 100 requests | 1 minute | Fair resource usage |

**Rate limit exceeded response (429):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 45  // seconds
}
```

### Quick Start - Authentication Flow

```bash
cd backend
source venv/bin/activate

# 1. Sign up
SIGNUP_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "role": "therapist"
  }')

# 2. Extract access token
ACCESS_TOKEN=$(echo $SIGNUP_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Use token to access protected endpoint
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Security Features

- **Password hashing:** Bcrypt with 12 rounds
- **Token rotation:** Refresh tokens automatically rotated on use
- **Rate limiting:** Login attempts limited to prevent brute force
- **JWT signing:** HS256 algorithm with 32-byte secret key
- **Token revocation:** Refresh tokens stored in database, can be revoked
- **SQL injection protection:** Parameterized queries via SQLAlchemy ORM
- **CORS:** Configured for frontend origin only

### Troubleshooting Authentication

#### "401 Unauthorized" - Token invalid or expired

**Symptoms:**
- API returns 401 when using access token
- Error message: "Could not validate credentials"

**Solutions:**
```bash
# 1. Check if token is expired (access tokens expire in 30 minutes)
# Use refresh token to get new access token:
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# 2. Verify token format in Authorization header:
# Correct: "Bearer eyJhbGc..."
# Wrong: "eyJhbGc..." (missing "Bearer" prefix)

# 3. Check for whitespace issues:
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -v  # verbose mode shows exact headers sent
```

#### "429 Too Many Requests" - Rate limit exceeded

**Symptoms:**
- Error: "rate_limit_exceeded"
- Response includes retry_after field

**Solutions:**
```bash
# Wait for retry_after seconds, then try again
# Login: Wait 60 seconds (5 requests/minute limit)
# Signup: Wait until next hour (3 requests/hour limit)
# Refresh: Wait 60 seconds (10 requests/minute limit)

# For development/testing, temporarily disable rate limiting:
# Comment out @limiter.limit() decorators in backend/app/auth/router.py
```

#### "Invalid refresh token" when using /refresh

**Common causes:**
1. **Token already used** (refresh tokens are single-use due to rotation)
2. **Token revoked** (user logged out)
3. **Token expired** (refresh tokens expire after 7 days)

**Solution:**
```bash
# If refresh token is invalid, user must log in again:
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

#### "Email already registered" during signup

**Symptoms:**
- HTTP 409 Conflict when creating account
- Email already exists in database

**Solutions:**
```bash
# 1. Use different email address
# 2. If you forgot password, use login endpoint:
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "existing@example.com", "password": "yourpassword"}'

# 3. For testing, manually delete user from database:
# psql $DATABASE_URL -c "DELETE FROM users WHERE email='test@example.com';"
```

#### JWT secret key changes invalidate all tokens

**Symptoms:**
- All users logged out after server restart
- All tokens return 401 Unauthorized

**Cause:**
- JWT_SECRET_KEY changed (or regenerated on restart if not set in .env)

**Solution:**
```bash
# Set persistent JWT_SECRET_KEY in backend/.env:
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> backend/.env

# Or use fixed key for development:
echo "JWT_SECRET_KEY=dev-secret-key-8a7f3e2d9c1b4a6e5f8d7c3b2a1e9f4d" >> backend/.env
```

#### Database migration errors

**Symptoms:**
- Server fails to start with SQLAlchemy errors
- Missing columns: hashed_password, is_active, role

**Solution:**
```bash
cd backend

# 1. Check current migration status:
alembic current

# 2. Apply all pending migrations:
alembic upgrade head

# 3. If migration fails, check database manually:
psql $DATABASE_URL -c "\d users"  # Show users table schema

# 4. Emergency rollback (if needed):
alembic downgrade -1  # Go back one migration
```

#### Password validation errors

**Symptoms:**
- 422 Unprocessable Entity during signup
- "Password must be at least 8 characters"

**Solution:**
```bash
# Ensure password meets requirements:
# - Minimum 8 characters
# - No other complexity requirements (for now)

# Valid example:
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "longenoughpassword",
    "full_name": "Test User",
    "role": "therapist"
  }'
```

#### Testing authentication in development

```bash
# Complete authentication flow test:

# 1. Signup
RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "role": "therapist"
  }')

# 2. Extract tokens (requires jq or python)
ACCESS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
REFRESH=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")

# 3. Test authenticated endpoint
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS"

# 4. Test token refresh
NEW_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}")

# 5. Extract new tokens
NEW_ACCESS=$(echo $NEW_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 6. Verify old refresh token is revoked (should fail with 401)
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}"  # This should return 401
```

## Cost Estimation

- Whisper API: $0.006/min → **~$0.18** for 30-min session
- GPT-4o extraction: ~$0.01-0.03 per session
- **Total: ~$0.20 per 30-minute session**
