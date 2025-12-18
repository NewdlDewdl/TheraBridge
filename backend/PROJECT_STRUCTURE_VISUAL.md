# Backend Project Structure - Visual Guide

## Complete Directory Tree

```
backend/
│
├── 📄 main.py                           # Local entry point (dev testing)
├── 📄 alembic.ini                       # Migration config
├── 📄 pytest.ini                        # Test config
├── 📄 requirements.txt                  # Python dependencies
├── 📄 .env                              # Environment (local)
├── 📄 .env.example                      # Environment template
├── 📄 .python-version                   # Python 3.13
├── 📄 README.md                         # Backend documentation
├── 📄 BACKEND_STRUCTURE_ANALYSIS.md     # Detailed analysis
├── 📄 ARCHITECTURE_QUICK_REFERENCE.md   # Quick lookup
│
├── 📁 app/                              # Main application package
│   │
│   ├── 📄 __init__.py
│   ├── 📄 main.py                       # FastAPI app initialization
│   ├── 📄 database.py                   # SQLAlchemy + session management
│   ├── 📄 config.py                     # Pydantic Settings (all env vars)
│   ├── 📄 validators.py                 # Input validation utilities
│   ├── 📄 logging_config.py             # Structured logging setup
│   │
│   ├── 📁 auth/                         # Authentication module
│   │   ├── __init__.py
│   │   ├── router.py                    # signup, login, refresh endpoints
│   │   ├── schemas.py                   # UserCreate, LoginRequest, TokenResponse
│   │   ├── utils.py                     # hash_password, create_token, verify_token
│   │   ├── dependencies.py              # get_current_user() dependency
│   │   ├── models.py                    # Auth-specific models (if any)
│   │   └── config.py                    # Auth configuration
│   │
│   ├── 📁 models/                       # Data models (database + API)
│   │   ├── __init__.py
│   │   ├── db_models.py                 # SQLAlchemy ORM models
│   │   │   ├── User
│   │   │   ├── Patient
│   │   │   ├── TherapistPatient (junction)
│   │   │   ├── TherapySession
│   │   │   └── AuthSession
│   │   ├── schemas.py                   # Pydantic request/response schemas
│   │   │   ├── Enums (UserRole, SessionStatus, MoodLevel)
│   │   │   ├── AI schemas (Strategy, Trigger, ActionItem, ExtractedNotes)
│   │   │   ├── CRUD schemas (SessionCreate, SessionResponse, etc.)
│   │   │   └── Helper schemas
│   │   └── analytics_models.py          # Analytics-specific schemas
│   │
│   ├── 📁 routers/                      # API endpoint definitions (one per resource)
│   │   ├── __init__.py
│   │   ├── sessions.py                  # Therapy sessions (CRUD + upload)
│   │   ├── patients.py                  # Patient management (CRUD)
│   │   ├── analytics.py                 # Analytics & reporting endpoints
│   │   └── cleanup.py                   # Admin cleanup operations
│   │
│   ├── 📁 services/                     # Business logic & external integrations
│   │   ├── __init__.py
│   │   ├── note_extraction.py           # OpenAI GPT-4o integration
│   │   ├── transcription.py             # Whisper transcription
│   │   ├── cleanup.py                   # Database cleanup logic
│   │   └── analytics.py                 # Analytics aggregation
│   │
│   ├── 📁 middleware/                   # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── rate_limit.py                # slowapi rate limiting config
│   │   ├── error_handler.py             # Global exception handlers
│   │   └── correlation_id.py            # X-Request-ID tracking
│   │
│   └── 📁 tasks/                        # Background jobs
│       ├── __init__.py
│       └── aggregation.py               # Analytics aggregation job definitions
│
├── 📁 tests/                            # Comprehensive test suite
│   │
│   ├── 📄 conftest.py                   # Global pytest fixtures
│   ├── 📄 test_auth_integration.py      # Full auth flow tests
│   ├── 📄 test_e2e_auth_flow.py         # End-to-end auth workflow
│   ├── 📄 test_cleanup.py               # Cleanup service tests
│   ├── 📄 test_config.py                # Config validation tests
│   ├── 📄 test_validators_example.py    # Validator unit tests
│   ├── 📄 test_rate_limiting.py         # Rate limit tests
│   ├── 📄 test_openai_mocks.py          # OpenAI mock tests
│   │
│   ├── 📁 routers/                      # Router-specific tests
│   │   ├── conftest.py                  # Router-level fixtures
│   │   ├── test_sessions.py             # Session endpoint tests
│   │   ├── test_patients.py             # Patient endpoint tests
│   │   ├── test_analytics.py            # Analytics endpoint tests
│   │   └── test_analytics_authorization.py  # Auth checks for analytics
│   │
│   ├── 📁 services/                     # Service unit tests
│   │   └── test_analytics.py            # Analytics service tests
│   │
│   ├── 📁 fixtures/                     # Test data generators
│   │   └── sample_transcripts.py        # Sample therapy transcripts
│   │
│   ├── 📁 mocks/                        # Mock services & fixtures
│   │   └── (Mock implementations)
│   │
│   ├── 📁 e2e/                          # End-to-end workflow tests
│   │   └── (Full workflow scenarios)
│   │
│   ├── 📁 performance/                  # Performance/load tests
│   │   └── (Performance test scenarios)
│   │
│   └── 📁 utils/                        # Test utilities
│       └── (Helper functions for tests)
│
├── 📁 alembic/                          # Database migrations (Alembic)
│   │
│   ├── 📄 env.py                        # Alembic runtime configuration
│   │
│   ├── 📁 versions/                     # Migration scripts
│   │   ├── (Initial schema migration)
│   │   ├── b2c3d4e5f6g7_add_missing_user_columns_and_junction.py
│   │   └── (Other future migrations...)
│   │
│   ├── 📄 script.py.mako               # Migration template
│   └── 📄 README.md                     # Migration documentation
│
├── 📁 migrations/                       # Migration analysis & notes
│   ├── analysis/
│   │   ├── integration_status.txt
│   │   └── topics_function_implementation.txt
│   └── (Documentation of migration decisions)
│
├── 📁 uploads/                          # Runtime file storage
│   └── 📁 audio/                        # Audio files (created at runtime)
│
├── 📁 scripts/                          # Utility scripts
│   └── (Helper scripts for dev/deployment)
│
├── 📁 venv/                             # Python virtual environment
│   └── (Dependency isolation)
│
└── 📁 htmlcov/                          # Test coverage reports
    └── (Coverage HTML output)
```

---

## Data Model Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User                                 │
│                                                             │
│  id (UUID)                                                  │
│  email (unique)                                             │
│  hashed_password                                            │
│  full_name, first_name, last_name                           │
│  role (therapist | patient | admin)                         │
│  is_active, is_verified                                     │
│  created_at, updated_at                                     │
└─────────────────────────────────────────────────────────────┘
        │                          │                      │
        │                          │                      │
        ├─────────────────┬────────┴───────────────┐      │
        │                 │                        │      │
        ↓                 ↓                        ↓      ↓
    AuthSession      TherapistPatient         Session   Session
    (1-to-many)      (many-to-many)           (as TP)   (as P)
    
    - user_id        - therapist_id
    - refresh_token  - patient_id
    - created_at     - relationship_type
    - expires_at     - is_active
                     - started_at
                     - ended_at


┌──────────────────────────────────────────────────────────────┐
│              TherapySession                                  │
│                                                              │
│  id (UUID)                                                   │
│  patient_id (FK → users.id)                                  │
│  therapist_id (FK → users.id)                                │
│  session_date                                                │
│  duration_seconds                                            │
│  audio_filename, audio_url                                   │
│  transcript_text, transcript_segments (JSONB)                │
│  extracted_notes (JSONB)                                     │
│  session_status                                              │
│  created_at, updated_at                                      │
└──────────────────────────────────────────────────────────────┘
        │                           │
        ↓                           ↓
    User (Therapist)          User (Patient)


┌──────────────────────────────────────────────────────────────┐
│              Patient (Legacy)                                │
│                                                              │
│  id (UUID)                                                   │
│  name                                                        │
│  email, phone                                                │
│  therapist_id (FK → users.id)                                │
│  created_at, updated_at                                      │
│                                                              │
│  Note: Being phased out in favor of User + TherapistPatient  │
└──────────────────────────────────────────────────────────────┘
```

---

## Request Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  HTTP Request (POST /api/sessions/)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Route Matching                                     │
│  (main.py: app.include_router)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Middleware Chain (executed in order)                       │
│  1. CorrelationIdMiddleware  → X-Request-ID                │
│  2. CORSMiddleware            → CORS headers               │
│  3. RateLimitMiddleware       → Check rate limits          │
│  4. ErrorHandlerMiddleware    → Exception catching         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Route Handler (sessions.py::create_session)               │
│  - Extract parameters from request body                    │
│  - Validate using Pydantic schema                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Dependency Injection                                       │
│  1. get_current_user() → Verify JWT, get User             │
│  2. get_db()          → Get AsyncSession from pool        │
│  3. get_service()     → Get service instance              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Validation Layer (validators.py)                          │
│  - validate_patient_exists(patient_id)                    │
│  - validate_required_string(name)                         │
│  - validate_email(email)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Business Logic (services/)                                │
│  - Call NoteExtractionService for transcript processing   │
│  - Call external APIs with retry logic                    │
│  - Return domain objects/schemas                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Database Operations (SQLAlchemy ORM)                       │
│  - Create ORM model: TherapySession(...)                   │
│  - db.add(session)                                        │
│  - await db.commit()                                      │
│  - await db.refresh(session)  ← Reload from DB            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Response Serialization                                     │
│  - ORM model → Pydantic schema                            │
│  - SessionResponse.model_validate(session)                │
│  - JSON encoding (pydantic automatic)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  HTTP Response                                              │
│  Status: 201 Created                                       │
│  Body: SessionResponse as JSON                            │
│  Headers: X-Request-ID, Content-Type, etc.                │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Patterns at a Glance

### 1. Async/Await Pattern
```python
async def endpoint(...) → async all the way down
    ├── await db.execute()
    ├── await service.async_method()
    └── await client.api_call()
```

### 2. Dependency Injection
```python
def endpoint(
    db: AsyncSession = Depends(get_db),        # DB session
    user: User = Depends(get_current_user),    # Auth check
    service = Depends(get_service)             # Service instance
):
    # All dependencies automatically provided by FastAPI
```

### 3. Schema Layering
```
Request JSON
    ↓
Pydantic Schema (SessionCreate) - Validates input
    ↓
ORM Model (db_models.TherapySession) - Database representation
    ↓
Pydantic Schema (SessionResponse) - Validates output
    ↓
Response JSON
```

### 4. Error Handling
```
Validation Error (Pydantic)  → 422 Unprocessable Entity
Authorization Error          → 401 Unauthorized
Not Found                     → 404 Not Found
Business Logic Error          → 400 Bad Request / 409 Conflict
Unhandled Exception          → 500 Internal Server Error (+ logging)
```

---

## File Naming Conventions

```
routers/
├── sessions.py          ← Plural (represents collection of resources)
├── patients.py
├── analytics.py
└── cleanup.py

services/
├── note_extraction.py   ← Descriptive, what it does
├── transcription.py
├── cleanup.py
└── analytics.py

models/
├── db_models.py         ← ORM models (database tables)
├── schemas.py           ← Pydantic schemas (API contracts)
└── analytics_models.py  ← Domain-specific models

tests/routers/
├── test_sessions.py     ← test_[module].py convention
├── test_patients.py
└── test_analytics.py
```

---

## Async Operations Timeline

```
Request arrives
    │
    ├─ Validate (sync) ──────────────────────────┐
    │                                            │
    ├─ Get current user (sync JWT verification) │
    │                                            │
    ├─ Database query (ASYNC) ◄──────────────────┘
    │  └─ await db.execute(select(...))
    │     └─ Yield control while waiting for DB
    │
    ├─ OpenAI API call (ASYNC)
    │  └─ await client.chat.completions.create()
    │     └─ Yield control while waiting for API
    │
    ├─ Database commit (ASYNC)
    │  └─ await db.commit()
    │
    └─ Return response
```

---

## Quick File Locations

| What I need | Where to find it |
|------------|-----------------|
| User model | `app/models/db_models.py::User` |
| Create endpoint | `app/routers/sessions.py::create_session()` |
| Email validation | `app/validators.py::validate_email()` |
| Authentication | `app/auth/router.py` |
| Database config | `app/database.py` |
| Environment vars | `app/config.py::Settings` |
| Test user fixture | `tests/conftest.py::test_user` |
| Session tests | `tests/routers/test_sessions.py` |
| Note extraction | `app/services/note_extraction.py` |
| Rate limiting | `app/middleware/rate_limit.py` |
| Error handling | `app/middleware/error_handler.py` |
| Migrations | `alembic/versions/` |

