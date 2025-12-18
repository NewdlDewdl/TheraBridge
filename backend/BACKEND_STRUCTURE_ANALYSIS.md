# TherapyBridge Backend Architecture Analysis

## Project Overview

**Location:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/`

**Technology Stack:**
- Framework: FastAPI (async Python web framework)
- Database: PostgreSQL (via Neon, async driver `asyncpg`)
- ORM: SQLAlchemy (async version)
- Authentication: JWT tokens (with refresh tokens)
- AI Integration: OpenAI API (GPT-4o for note extraction)
- Migrations: Alembic
- Testing: pytest with async support

---

## 1. Directory Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI app initialization, lifespan, health checks
│   ├── database.py              # SQLAlchemy engine, session factories, get_db() dependency
│   ├── config.py                # Pydantic Settings for all configuration (centralized)
│   ├── validators.py            # Input validation utilities (email, phone, UUID checks)
│   ├── logging_config.py        # Structured logging setup
│   │
│   ├── auth/                    # Authentication module
│   │   ├── __init__.py
│   │   ├── router.py            # Auth endpoints (signup, login, refresh token)
│   │   ├── schemas.py           # Auth request/response models
│   │   ├── models.py            # Auth-specific models (if any)
│   │   ├── utils.py             # Password hashing, JWT encoding/decoding
│   │   ├── dependencies.py      # FastAPI dependency injection (get_current_user)
│   │   └── config.py            # Auth-specific configuration
│   │
│   ├── models/                  # Data models (database + API schemas)
│   │   ├── __init__.py
│   │   ├── db_models.py         # SQLAlchemy ORM models (User, Patient, TherapySession, etc.)
│   │   ├── schemas.py           # Pydantic schemas (all API request/response models)
│   │   └── analytics_models.py  # Analytics-specific models
│   │
│   ├── routers/                 # API endpoint modules (one per resource)
│   │   ├── __init__.py
│   │   ├── sessions.py          # Therapy session endpoints
│   │   ├── patients.py          # Patient management endpoints
│   │   ├── analytics.py         # Analytics endpoints
│   │   └── cleanup.py           # Admin cleanup endpoints
│   │
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── note_extraction.py   # OpenAI-powered note extraction from transcripts
│   │   ├── transcription.py     # Audio transcription service
│   │   ├── cleanup.py           # Database cleanup service
│   │   └── analytics.py         # Analytics aggregation service
│   │
│   ├── middleware/              # Custom middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py        # Rate limiting configuration
│   │   ├── error_handler.py     # Global exception handlers
│   │   └── correlation_id.py    # Request ID tracking for logging
│   │
│   └── tasks/                   # Background job definitions
│       ├── __init__.py
│       └── aggregation.py       # Analytics aggregation jobs
│
├── tests/                        # Comprehensive test suite
│   ├── conftest.py              # pytest fixtures (database, auth, client setup)
│   ├── fixtures/                # Test data generators
│   ├── mocks/                   # Mock services for testing
│   ├── routers/                 # Router-specific tests
│   ├── services/                # Service-specific tests
│   ├── e2e/                     # End-to-end tests
│   ├── performance/             # Performance tests
│   └── [test_*.py]              # Integration and unit tests
│
├── alembic/                      # Database migrations
│   ├── versions/                # Migration scripts
│   └── env.py                   # Alembic configuration
│
├── migrations/                   # Analysis and notes on migrations
├── scripts/                      # Utility scripts
├── uploads/audio/               # Runtime audio file storage
├── main.py                       # Entry point (optional, for local dev)
├── alembic.ini                  # Alembic config file
├── pytest.ini                   # pytest configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── .python-version              # Python version (3.13)
└── README.md                    # Backend documentation
```

---

## 2. Core Organization Patterns

### 2.1 Separation of Concerns

The backend strictly separates concerns across multiple layers:

| Layer | Purpose | Files |
|-------|---------|-------|
| **API Layer** | FastAPI endpoints | `routers/*.py` |
| **Schema Layer** | Request/response validation | `models/schemas.py` |
| **Database Layer** | ORM models | `models/db_models.py` |
| **Business Logic** | Core processing | `services/*.py` |
| **Validation** | Input sanitization | `validators.py` |
| **Configuration** | Environment setup | `config.py` |
| **Middleware** | Cross-cutting concerns | `middleware/*.py` |

### 2.2 Naming Conventions

**Files:**
- `routers/sessions.py` - Plural resource name
- `services/note_extraction.py` - Descriptive snake_case
- `models/db_models.py` vs `models/schemas.py` - Clear distinction

**Classes:**
- ORM Models: PascalCase, match table names
  - `User`, `Patient`, `TherapySession`, `TherapistPatient`
- Pydantic Schemas: PascalCase with descriptive suffix
  - `SessionCreate`, `SessionResponse`, `ExtractedNotes`
- Enums: snake_case
  - `UserRole`, `SessionStatus`, `MoodLevel`

**Functions:**
- Async endpoint handlers: `async def create_session(...)`
- Services: `async def extract_notes_from_transcript(...)`
- Validators: `def validate_email(email: str) -> Optional[str]`

**Route Naming:**
- POST `/api/patients/` - Create
- GET `/api/patients/{patient_id}` - Retrieve
- PUT/PATCH `/api/patients/{patient_id}` - Update
- DELETE `/api/patients/{patient_id}` - Delete
- GET `/api/patients/` - List

---

## 3. File-by-File Organization Guide

### 3.1 Database Configuration (`app/database.py`)

**Responsibilities:**
- Async engine setup with connection pooling
- Sync engine for auth operations
- Session factory creation
- `get_db()` dependency for endpoint injection

**Key Configuration:**
- Connection pooling (pool_size, max_overflow, pool_timeout)
- SSL enforcement (required for Neon PostgreSQL)
- `pool_pre_ping=True` to verify connections
- Separate async/sync engines (async for most endpoints, sync for auth)

**Pattern - Usage in Routers:**
```python
@router.post("/")
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db)  # Automatic dependency injection
):
    # Use db to query/create/update
    result = await db.execute(select(Model))
    return result
```

### 3.2 Configuration Module (`app/config.py`)

**Design:**
- Centralized Pydantic `BaseSettings` for all env vars
- Single `settings` instance imported everywhere
- Environment profiles: development, staging, production
- Post-init validation for security constraints

**Key Sections:**
- Environment configuration (DEBUG, ENVIRONMENT)
- Database settings (URL, pool configuration)
- OpenAI settings (API key, model, timeout, retries)
- JWT settings (secret, algorithm, expiration)
- CORS configuration (allowed origins)
- Upload settings (directory, max size, formats)
- Cleanup settings (retention periods)
- Rate limiting configuration (login, signup, general API)
- Logging configuration (level, format)

**Usage Pattern:**
```python
from app.config import settings

# Access any setting
if settings.is_production:
    # Production-specific code
    debug_mode = False
```

### 3.3 ORM Models (`app/models/db_models.py`)

**Key Models:**

1. **User** - Represents therapists, patients, and admins
   - Fields: id (UUID), email, hashed_password, full_name, first_name, last_name
   - Role: therapist, patient, admin (enum)
   - is_active, is_verified, created_at, updated_at
   - Relationships: auth_sessions, patients_assigned, therapists_assigned

2. **Patient** - Patient records (legacy, now associated via TherapistPatient)
   - Fields: id, name, email, phone, therapist_id
   - Note: Being phased out for User-based patient tracking

3. **TherapistPatient** - Many-to-many junction table
   - Fields: therapist_id, patient_id, relationship_type, is_active, started_at, ended_at
   - Relationships: back-references to User as therapist and patient
   - UNIQUE constraint: (therapist_id, patient_id)

4. **TherapySession** - Therapy session records
   - Fields: id, patient_id, therapist_id, session_date, duration_seconds
   - Audio data: audio_filename, audio_url
   - Transcription: transcript_text, transcript_segments (JSONB)
   - Extracted notes: extracted_notes (JSONB)
   - Status: session_status (enum)

5. **AuthSession** - JWT refresh token tracking
   - Fields: id, user_id, refresh_token, created_at, expires_at
   - Relationship: back-reference to User

**Column Types Used:**
- `SQLUUID(as_uuid=True)` - UUIDs (native PostgreSQL UUID type)
- `String(N)` - Varchar with max length
- `Text` - Unlimited text (for transcripts, notes)
- `JSONB` - PostgreSQL native JSON (for complex structures)
- `DateTime` - Timestamps with UTC default
- `Enum` - Database enum (requires SQLAlchemy Enum)
- `Boolean` - True/false flags
- `ForeignKey` - Relationships with cascade options
- `Index=True` - Query optimization on frequently searched fields

**Relationships Pattern:**
```python
class User(Base):
    __tablename__ = "users"
    
    # One-to-many: User has multiple auth sessions
    auth_sessions = relationship(
        "AuthSession", 
        back_populates="user", 
        cascade="all, delete-orphan"  # Deleting user deletes sessions
    )
    
    # Many-to-many: User (therapist) has multiple patients
    patients_assigned = relationship(
        "TherapistPatient",
        foreign_keys="TherapistPatient.therapist_id",
        back_populates="therapist",
        cascade="all, delete-orphan"
    )
```

### 3.4 API Schemas (`app/models/schemas.py`)

**Organization:**
- Enums first (UserRole, SessionStatus, MoodLevel, etc.)
- AI extraction schemas (Strategy, Trigger, ActionItem, etc.)
- Database model schemas (SessionBase, SessionCreate, SessionResponse, etc.)
- Bulk operation schemas
- Helper schemas (pagination, error responses)

**Schema Inheritance Pattern:**
```python
# Base schema with common fields
class SessionBase(BaseModel):
    patient_id: UUID
    session_date: datetime
    
# For create requests (minimal fields)
class SessionCreate(SessionBase):
    # Only fields needed to create
    pass

# For responses (includes generated fields)
class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    status: SessionStatus
    
    # Tell Pydantic to map DB model -> schema
    model_config = ConfigDict(from_attributes=True)
```

**Pydantic Configuration:**
```python
model_config = ConfigDict(
    from_attributes=True,    # Allow ORM model conversion
    json_schema_extra={...}  # OpenAPI documentation
)
```

### 3.5 Validators (`app/validators.py`)

**Functions Provided:**
- `validate_email(email)` - RFC 5322 compliant email validation
- `validate_phone(phone)` - International phone number validation
- `validate_required_string(string, min_length, max_length)` - String validation
- `sanitize_filename(filename)` - Remove unsafe characters
- `validate_audio_file_header(data)` - Magic bytes validation
- `validate_patient_exists(patient_id, db)` - UUID existence check
- `validate_session_exists(session_id, db)` - Session lookup
- `validate_therapist_exists(therapist_id, db)` - Therapist role verification

**Usage Pattern:**
```python
from app.validators import validate_email, validate_required_string

@router.post("/")
async def create_item(data: ItemCreate):
    # Validate email format
    data.email = validate_email(data.email)
    
    # Validate name length
    data.name = validate_required_string(
        data.name, 
        min_length=1, 
        max_length=255
    )
```

### 3.6 Routers (`app/routers/sessions.py`, etc.)

**Structure:**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models.schemas import SessionCreate, SessionResponse
from app.models import db_models
from app.validators import validate_...
from app.middleware.rate_limit import limiter

router = APIRouter()

@router.post("/", response_model=SessionResponse)
@limiter.limit("100/minute")  # Rate limiting
async def create_session(
    session: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new therapy session"""
    # Validation
    validated_data = validate_required_string(session.name)
    
    # Create ORM model
    db_session = db_models.TherapySession(**session.model_dump())
    
    # Save to database
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    # Return as schema (ORM -> Pydantic)
    return SessionResponse.model_validate(db_session)
```

**Key Patterns:**
- All endpoints are `async def`
- `Depends(get_db)` for database session
- `Depends(get_current_user)` for authentication
- `@limiter.limit("X/period")` for rate limiting
- Response models for type validation and OpenAPI docs
- HTTPException for error responses

### 3.7 Services (`app/services/`)

**note_extraction.py:**
- `NoteExtractionService` class with async methods
- `extract_notes_from_transcript(transcript: str) -> ExtractedNotes`
- Handles OpenAI API calls with retry logic
- Parses structured JSON responses
- Handles rate limiting and API errors

**transcription.py:**
- `transcribe_audio_file(file_path: str) -> str`
- Calls Whisper API or local model

**cleanup.py:**
- `delete_failed_sessions(days: int) -> int`
- `delete_orphaned_files(hours: int) -> int`
- Implements retention policy logic

**analytics.py:**
- `aggregate_daily_metrics(date: str) -> Dict`
- Calculates session statistics, mood trends, etc.

**Service Pattern:**
```python
class NoteExtractionService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def extract_notes(self, transcript: str) -> ExtractedNotes:
        # Call OpenAI API
        response = await self.client.chat.completions.create(...)
        
        # Parse JSON response
        notes = ExtractedNotes.model_validate_json(response.content)
        
        # Return validated schema
        return notes

# Singleton pattern for dependency injection
def get_extraction_service() -> NoteExtractionService:
    return NoteExtractionService()

# Usage in router
from app.services.note_extraction import get_extraction_service

@router.post("/extract")
async def extract_notes(
    session_id: UUID,
    service = Depends(get_extraction_service),
    db: AsyncSession = Depends(get_db)
):
    notes = await service.extract_notes(transcript)
```

### 3.8 Middleware (`app/middleware/`)

**rate_limit.py:**
- Uses `slowapi` library
- Configurable limits per endpoint
- Custom exception handler for 429 responses

**error_handler.py:**
- Global exception handler registration
- Converts exceptions to HTTP responses
- Ensures security (no PHI in error messages in production)

**correlation_id.py:**
- Generates/captures X-Request-ID header
- Stores ID in context variable for logging
- Adds ID to response headers

**Usage in main.py:**
```python
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.error_handler import register_exception_handlers

# Add middleware (order matters - correlation ID first)
app.add_middleware(CorrelationIdMiddleware)

# Register exception handlers
register_exception_handlers(app)
```

### 3.9 Main Application (`app/main.py`)

**Responsibilities:**
1. Load environment variables
2. Configure logging
3. Create FastAPI app with lifespan
4. Register middleware (order: correlation ID, CORS)
5. Register exception handlers
6. Include routers with prefixes
7. Define health check endpoints

**Lifespan Pattern:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting app")
    await init_db()
    
    yield  # App runs here
    
    # Shutdown
    logger.info("Shutting down")
    await close_db()

app = FastAPI(lifespan=lifespan)
```

**Health Check Endpoints:**
- `GET /` - Service info
- `GET /health` - Detailed health (DB, OpenAI, pool status)
- `GET /ready` - Readiness probe (DB connectivity only)
- `GET /live` - Liveness probe (always passes unless crashed)

### 3.10 Authentication (`app/auth/`)

**router.py:**
- `POST /api/v1/auth/signup` - Create new user
- `POST /api/v1/auth/login` - Get access token
- `POST /api/v1/auth/refresh` - Refresh access token

**utils.py:**
- `hash_password(password: str) -> str` - BCrypt hashing
- `verify_password(plain, hashed) -> bool` - Verification
- `create_access_token(user_id: UUID, expires_in: int) -> str` - JWT encoding
- `verify_token(token: str) -> UUID` - JWT decoding

**dependencies.py:**
- `get_current_user() -> User` - Extract user from Bearer token
- Raises HTTPException 401 if token invalid/expired

**schemas.py:**
- `UserCreate` - Signup request (email, password, first_name, last_name, role)
- `UserResponse` - User object (all public fields)
- `LoginRequest` - Login request (email, password)
- `TokenResponse` - Token response (access_token, refresh_token, expires_in)

---

## 4. Import Patterns & Dependencies

### 4.1 Standard Import Order

1. Python standard library
2. Third-party libraries
3. Application modules

```python
# Standard
import os
import logging
from datetime import datetime
from typing import List, Optional

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Application
from app.database import get_db
from app.models import db_models
from app.models.schemas import SessionCreate, SessionResponse
from app.validators import validate_email
from app.services.note_extraction import get_extraction_service
```

### 4.2 Dependency Injection Pattern

FastAPI uses the Depends system for dependency injection:

```python
# Define dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise

# Use in endpoint
@router.get("/items")
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = Query(default=10, le=100)
):
    # db and current_user are automatically injected
    result = await db.execute(select(Item))
```

### 4.3 Service Factory Pattern

Services are often singleton factories:

```python
# Service definition
class NoteExtractionService:
    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def extract(self, transcript: str) -> ExtractedNotes:
        ...

# Factory function
def get_extraction_service() -> NoteExtractionService:
    return NoteExtractionService()  # Or cached singleton

# Usage
@router.post("/extract")
async def extract(
    session_id: UUID,
    service = Depends(get_extraction_service)
):
    notes = await service.extract(transcript)
```

---

## 5. Configuration & Environment Setup

### 5.1 Configuration Hierarchy

1. **Default values** in `Settings` class
2. **Environment variables** from `.env` file
3. **Runtime validation** in `model_post_init()`

### 5.2 Environment Variables

**Critical (required):**
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key

**Security (production):**
- `DEBUG=false` - Must be false in production
- `SQL_ECHO=false` - Must be false in production
- `JWT_SECRET_KEY` - Should be >32 chars in production
- `ENVIRONMENT=production` - Enables security checks

**Database Pool:**
- `DB_POOL_SIZE=20` - Connections to maintain
- `DB_MAX_OVERFLOW=10` - Extra connections when pool full
- `DB_POOL_TIMEOUT=30` - Wait time for available connection
- `DB_POOL_RECYCLE=3600` - Recycle connections after 1 hour

**Authentication:**
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `REFRESH_TOKEN_EXPIRE_DAYS=7`

**CORS:**
- `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`

**Rate Limiting:**
- `RATE_LIMIT_LOGIN=5/minute`
- `RATE_LIMIT_SIGNUP=3/hour`
- `RATE_LIMIT_REFRESH=10/minute`
- `RATE_LIMIT_API=100/minute`

---

## 6. Testing Structure

### 6.1 Test Organization

```
tests/
├── conftest.py                  # Global fixtures (db, auth, client)
├── fixtures/                    # Reusable test data generators
│   └── sample_transcripts.py
├── routers/                     # Router-specific tests
│   ├── conftest.py              # Router fixture overrides
│   ├── test_sessions.py
│   ├── test_patients.py
│   ├── test_analytics.py
│   └── test_analytics_authorization.py
├── services/                    # Service unit tests
│   └── test_analytics.py
├── e2e/                         # End-to-end workflow tests
├── mocks/                       # Mock services and fixtures
└── test_auth_integration.py    # Full auth flow tests
```

### 6.2 Test Database Configuration

**Key Points:**
- In-memory SQLite (`test.db`) for fast tests
- Separate `TestingSessionLocal` factory
- Auto-cleanup between tests via fixtures
- Database reset in `conftest.py`

**Fixture Pattern:**
```python
@pytest.fixture
async def test_db():
    # Create test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def test_user(test_db):
    # Create a test user
    user = User(email="test@example.com", ...)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user
```

### 6.3 Test Client Pattern

```python
@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)

def test_create_session(client, test_user):
    response = client.post(
        "/api/sessions/",
        json={"patient_id": "...", "session_date": "..."},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
```

---

## 7. Design Patterns Summary

| Pattern | Usage | Example |
|---------|-------|---------|
| **Dependency Injection** | Automatic resource provision | `Depends(get_db)`, `Depends(get_current_user)` |
| **Factory Pattern** | Singleton service creation | `get_extraction_service()` |
| **Schema Inheritance** | DRY API schemas | `SessionBase` → `SessionCreate` → `SessionResponse` |
| **Async Context Manager** | Lifespan management | `@asynccontextmanager` in main.py |
| **Middleware Chain** | Cross-cutting concerns | Correlation ID, CORS, error handling |
| **Middleware Decorator** | Rate limiting | `@limiter.limit("100/minute")` |
| **Exception Handlers** | Centralized error handling | `register_exception_handlers(app)` |
| **Validator Functions** | Reusable validation | Import from `validators.py` |
| **Service Classes** | Business logic encapsulation | `NoteExtractionService` |
| **ORM Relationships** | Database relationships | `relationship()` with back_populates |

---

## 8. Key Conventions for New Features

### When Adding Treatment Plans Feature:

1. **Create Database Model** (`app/models/db_models.py`):
   ```python
   class TreatmentPlan(Base):
       __tablename__ = "treatment_plans"
       id = Column(SQLUUID, primary_key=True)
       patient_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"))
       therapist_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"))
       # ... other fields
       patient = relationship("User", foreign_keys=[patient_id])
       therapist = relationship("User", foreign_keys=[therapist_id])
   ```

2. **Create Pydantic Schemas** (`app/models/schemas.py`):
   ```python
   class TreatmentPlanBase(BaseModel):
       patient_id: UUID
       goals: List[str]
   
   class TreatmentPlanCreate(TreatmentPlanBase):
       pass
   
   class TreatmentPlanResponse(TreatmentPlanBase):
       id: UUID
       created_at: datetime
       model_config = ConfigDict(from_attributes=True)
   ```

3. **Create Router** (`app/routers/treatment_plans.py`):
   ```python
   router = APIRouter()
   
   @router.post("/", response_model=TreatmentPlanResponse)
   async def create_treatment_plan(
       plan: TreatmentPlanCreate,
       db: AsyncSession = Depends(get_db),
       current_user = Depends(get_current_user)
   ):
       # Implementation
   ```

4. **Include Router** in `app/main.py`:
   ```python
   from app.routers import treatment_plans
   app.include_router(treatment_plans.router, prefix="/api/treatment-plans")
   ```

5. **Create Tests** (`tests/routers/test_treatment_plans.py`):
   - Test create, read, update, delete
   - Test authorization
   - Test validation
   - Test edge cases

6. **Add Validators** as needed to `app/validators.py`:
   ```python
   def validate_treatment_goal(goal: str) -> str:
       goal = validate_required_string(goal, min_length=5, max_length=500)
       return goal
   ```

7. **Create Migration** (`alembic/versions/`):
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add treatment_plans table"
   alembic upgrade head
   ```

---

## Summary

The backend is organized as a **layered architecture** with clear separation between:
- **API Layer** (routers) - Handles HTTP requests
- **Schema Layer** (models/schemas.py) - Validates input/output
- **Database Layer** (models/db_models.py) - Defines data structure
- **Business Logic Layer** (services) - Implements core functionality
- **Cross-cutting Concerns** (middleware, validators, config)

This structure makes it easy to:
- Add new features (following the established patterns)
- Test components independently
- Maintain security (PHI protection, input validation)
- Scale horizontally (stateless design, async operations)

When implementing **Treatment Plans**, follow the same patterns and place code in the appropriate layer.
