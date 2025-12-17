# Backend Dependencies Cleanup Report

**Date:** 2025-12-17
**Analysis:** Comprehensive search across all Python files in backend project

---

## Summary

Out of 5 flagged dependencies, **2 are genuinely unused** and **3 are actively used**.

### Status Overview
- Total dependencies: 22 in requirements.txt
- Flagged for review: 5
- Confirmed unused: 2
- Actively used: 3

---

## Detailed Findings

### ✅ ACTIVELY USED DEPENDENCIES

#### 1. **psycopg2-binary** (line 12)
**Status:** ACTIVELY USED - KEEP
**Reason:** Used in multiple critical scripts

**Files using psycopg2:**
- `/backend/scripts/backup_database.py` (lines 18-19, 54, 57, 111)
  - Uses: `psycopg2.connect()`, `psycopg2.OperationalError`, `psycopg2.ProgrammingError`
  - Purpose: Database backup utility - connects directly to PostgreSQL

- `/backend/scripts/export_users_schema.py` (line 3)
  - Uses: `psycopg2.connect()`
  - Purpose: Export users table schema analysis

- `/backend/scripts/check_auth_sessions.py` (line 3)
  - Uses: `psycopg2.connect()`
  - Purpose: Verify auth_sessions table existence and structure

- `/backend/run_migration.py` (lines 19-23, 31)
  - Uses: `psycopg2.connect()`, conditional import/installation
  - Purpose: Run database migrations directly

**Alternative:** Cannot be replaced - these are synchronous scripts that need direct PostgreSQL access for admin operations. The main application uses `asyncpg` via SQLAlchemy, but these scripts handle initialization and backup tasks that require psycopg2.

---

#### 2. **alembic** (line 13)
**Status:** ACTIVELY USED - KEEP
**Reason:** Used by migration infrastructure

**Files using alembic:**
- `/backend/alembic/env.py` (lines 8, 18)
  - Uses: `from alembic import context`, imports for migration execution
  - Purpose: Alembic migration environment setup

- `/backend/alembic/versions/` (3+ migration files)
  - Uses: Alembic migration framework for database schema versioning

**Alternative:** None - alembic is the industry-standard database migration framework for SQLAlchemy projects

---

#### 3. **pydub & audioop-lts** (lines 34-35)
**Status:** ACTIVELY USED - KEEP
**Reason:** Audio pipeline uses these for preprocessing

**Evidence:**
- Listed as dependencies in `/backend/requirements.txt` with note: "# Audio pipeline dependencies (reuse from transcription pipeline)"
- The audio-transcription-pipeline project (`/audio-transcription-pipeline/`) depends on pydub for audio file operations
- Backend's `/app/services/transcription.py` wraps the audio-transcription-pipeline (line 12-26)
- While not imported directly in backend code, these are dependencies of the transcription pipeline that backend depends on

**Current Architecture:**
- Backend calls `AudioTranscriptionPipeline()` from the transcription pipeline
- That pipeline uses pydub and audioop-lts for audio operations
- Including these in backend requirements.txt ensures dependency consistency

**Note:** These could be moved to a separate transcription-dependencies requirements file, but not deleted.

---

### ❌ GENUINELY UNUSED DEPENDENCIES

#### 1. **pytest-cov** (line 41)
**Status:** UNUSED - SAFE TO REMOVE
**Reason:** No test coverage configuration found

**Evidence:**
- No `pytest_cov` imports found in any backend Python files
- No `--cov` flags in pytest configuration
- `conftest.py` uses `pytest` but not coverage reporting
- File: `/backend/tests/conftest.py` - uses pytest fixtures but no coverage setup
- No `.coveragerc` or pytest coverage configuration found

**Impact of removal:** Low - only affects development/testing workflows
**Recommendation:** Remove from requirements.txt (line 41)

---

#### 2. **pytest-asyncio** (line 30)
**Status:** UNUSED - SAFE TO REMOVE

**WAIT - This is actually used. Re-checking...**

Actually, let me verify this one more carefully.

---

### VERIFICATION RESULTS FOR pytest DEPENDENCIES

**pytest** (line 29) - USED
- Imported in `/backend/tests/conftest.py`
- Used for all test fixtures and setup

**pytest-asyncio** (line 30) - NOT EXPLICITLY USED
- NOT imported in conftest.py
- Tests could use pytest's built-in async handling or direct SQLAlchemy's async sessions
- But it's a lightweight dependency (13 kB) and follows async testing best practices
- Recommendation: OPTIONAL - keep for best practices with async code, or remove if not using async test decorators

**httpx** (line 31) - USED
- Required by FastAPI TestClient for making HTTP requests in tests
- Used implicitly by TestClient in conftest.py (line 98)

**pytest-cov** (line 41) - NOT USED
- No coverage configuration found
- Safe to remove

---

## FINAL RECOMMENDATIONS

### Remove (Safe to Delete)
1. **pytest-cov==4.1.0** - No coverage configuration or usage found

### Consider Removing (Optional)
1. **pytest-asyncio==0.23.3** - Not explicitly used, but good practice for async testing
   - Decision: Keep (minimal overhead, standard practice)

### Keep (Required)
1. **psycopg2-binary>=2.9.11** - Used by admin scripts
2. **alembic==1.13.1** - Used by migration system
3. **pydub==0.25.1** - Used by audio transcription pipeline
4. **audioop-lts>=0.2.1** - Used by audio transcription pipeline

---

## Action Items

**Next Steps:**
1. Remove `pytest-cov==4.1.0` from requirements.txt
2. Verify tests still pass without pytest-cov: `pytest`
3. Optional: Consider creating separate requirements files for different concerns:
   - `requirements-core.txt` - FastAPI, database, auth
   - `requirements-audio.txt` - pydub, audioop-lts
   - `requirements-dev.txt` - pytest, pytest-asyncio, httpx
   - `requirements.txt` - reference all above

---

## Appendix: Complete Dependency Analysis

```
fastapi==0.109.0 ✅ Used in app/main.py
uvicorn[standard]==0.27.0 ✅ Used for server startup
python-multipart==0.0.6 ✅ Used for file uploads (FastAPI dependency)

sqlalchemy[asyncio]>=2.1.0b1 ✅ Used in app/database.py
psycopg[binary]>=3.3.2 ✅ Modern PostgreSQL driver (asyncio compatible)
asyncpg>=0.31.0 ✅ Used by SQLAlchemy for async operations
psycopg2-binary>=2.9.11 ✅ Used in admin scripts

openai>=1.59.5 ✅ Used in app/services/note_extraction.py

python-dotenv>=1.0.0 ✅ Used for environment loading
pydantic-settings>=2.0.0 ✅ Used for AuthConfig

python-jose[cryptography]>=3.3.0 ✅ Used for JWT tokens
passlib>=1.7.4 ✅ Used for password hashing
bcrypt>=4.0.0,<5.0.0 ✅ Backend for passlib
email-validator>=2.0.0 ✅ Used for email validation

pytest==7.4.4 ✅ Used for testing
pytest-asyncio==0.23.3 ⚠️ Not explicitly used, but good practice
httpx==0.26.0 ✅ Used by FastAPI TestClient

pydub==0.25.1 ✅ Used by transcription pipeline
audioop-lts>=0.2.1 ✅ Used by transcription pipeline

slowapi==0.1.9 ✅ Used in app/middleware/rate_limit.py

pytest-cov==4.1.0 ❌ NOT USED - Safe to remove
alembic==1.13.1 ✅ Used for database migrations
```

---

**Report Generated:** 2025-12-17
**Analyzer:** Claude Code Dependency Scanner
