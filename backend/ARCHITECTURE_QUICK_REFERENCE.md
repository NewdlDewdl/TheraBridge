# Backend Architecture Quick Reference

## At a Glance

```
HTTP Request
    ↓
[Route Handler] → [Middleware Chain]
    ↓
[Dependency Injection] (auth, database)
    ↓
[Input Validation] (validators.py)
    ↓
[Business Logic] (services/)
    ↓
[Database Operations] (db_models.py + SQLAlchemy)
    ↓
[Response Schema] (schemas.py)
    ↓
HTTP Response
```

---

## Key Files & Their Roles

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `main.py` | App initialization | FastAPI instance, lifespan, health checks |
| `database.py` | DB connection | `get_db()` dependency, async/sync engines |
| `config.py` | Configuration | `Settings` class, all env vars |
| `validators.py` | Input validation | `validate_email()`, `validate_phone()`, etc. |
| `models/db_models.py` | Database schema | `User`, `Patient`, `TherapySession`, `TherapistPatient`, `AuthSession` |
| `models/schemas.py` | API contracts | `SessionCreate`, `SessionResponse`, `ExtractedNotes`, etc. |
| `routers/sessions.py` | Session endpoints | CRUD operations for therapy sessions |
| `routers/patients.py` | Patient endpoints | Patient management |
| `routers/analytics.py` | Analytics endpoints | Session statistics, mood trends |
| `auth/router.py` | Auth endpoints | signup, login, refresh token |
| `services/note_extraction.py` | Note extraction | OpenAI integration for clinical notes |
| `middleware/` | Cross-cutting | Rate limiting, error handling, correlation IDs |

---

## Data Flow Example: Create Session

```
POST /api/sessions/
    ↓
[sessions.py::create_session()]
    ├── Validate input (SessionCreate schema)
    ├── Check auth (get_current_user dependency)
    ├── Get DB session (get_db dependency)
    ├── Validate patient exists (validators.py)
    ├── Create ORM model (db_models.TherapySession)
    ├── Save to database (await db.commit())
    ├── Convert ORM → Schema (SessionResponse)
    ↓
200 OK with SessionResponse JSON
```

---

## Testing Organization

```
tests/
├── conftest.py                 ← Global fixtures
├── routers/                    ← Test each endpoint
│   ├── test_sessions.py
│   ├── test_patients.py
│   └── test_analytics.py
├── services/                   ← Test business logic
├── e2e/                        ← Full workflow tests
└── test_auth_integration.py    ← Auth flow tests
```

**Key Fixture Pattern:**
```python
@pytest.fixture
async def test_user(test_db):
    user = User(email="test@example.com", role=UserRole.therapist)
    test_db.add(user)
    await test_db.commit()
    return user
```

---

## Common Operations

### Add a New Endpoint

1. Add schema in `models/schemas.py`
2. Add route in `routers/new_resource.py`
3. Include router in `main.py`
4. Add validators if needed
5. Add tests in `tests/routers/test_new_resource.py`

### Add a Database Model

1. Define model in `models/db_models.py`
2. Create migration: `alembic revision --autogenerate -m "Add table"`
3. Run migration: `alembic upgrade head`
4. Add schemas for CRUD in `models/schemas.py`
5. Create router in `routers/`

### Call External API (OpenAI, etc.)

1. Create service class in `services/`
2. Use dependency injection: `Depends(get_service)`
3. Handle errors (rate limits, timeouts)
4. Return validated response schema

### Validate User Input

```python
from app.validators import validate_email, validate_required_string

# In endpoint
email = validate_email(user.email)  # Raises HTTPException if invalid
name = validate_required_string(user.name, min_length=1, max_length=255)
```

---

## Database Relationships

### User ← TherapistPatient → User
```
therapist (User)
    ↓
TherapistPatient (junction table)
    ↓
patient (User)
```
Allows multiple therapists per patient.

### User → TherapySession ← Patient
```
therapist_id (User.id)
patient_id (Patient.id)
    ↓
TherapySession
```
Records who provided therapy to whom.

### User → AuthSession
```
One-to-many: User has multiple auth sessions
(for JWT refresh token management)
```

---

## Async/Await Pattern

All database operations and API calls are **async**:

```python
# Correct - wait for async operations
async def create_item(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))  # ← await
    await db.commit()                         # ← await
    return result

# Wrong - forgetting await
async def create_item(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(Item))  # ✗ Missing await
```

---

## Configuration Loading Order

1. Read `.env` file
2. Load into `Settings` class
3. Run validators on each field
4. Run `model_post_init()` for security checks
5. Access via `from app.config import settings`

**Access anywhere:**
```python
from app.config import settings

if settings.is_production:
    api_timeout = settings.OPENAI_TIMEOUT
```

---

## Error Handling

### Endpoint Level
```python
@router.post("/")
async def create(data: ItemCreate):
    if not data.name:
        raise HTTPException(status_code=400, detail="Name required")
    return {"success": True}
```

### Global Handler
Registered in `middleware/error_handler.py`:
- Catches all exceptions
- Logs with correlation ID
- Returns safe error response (no PHI in production)

### Validation Level
```python
from app.validators import validate_email

email = validate_email(user.email)  # Raises HTTPException 400
```

---

## Security Notes

1. **Always validate input** - Use `validators.py` functions
2. **Check auth** - Use `Depends(get_current_user)`
3. **No SQL injection** - SQLAlchemy ORM handles escaping
4. **No PHI in logs** - Production disables SQL_ECHO, debug mode
5. **Rate limiting** - Applied to auth endpoints
6. **HTTPS only** - SSL enforced on database connection
7. **JWT validation** - All endpoints verify token signature

---

## Common Gotchas

| Issue | Solution |
|-------|----------|
| "No module named 'app'" | Run from backend dir: `cd backend` |
| Async/await errors | Always `await` DB operations |
| Migration conflicts | Run `alembic downgrade -1` before retry |
| Test DB not isolated | Check `conftest.py` cleanup logic |
| Correlation ID missing | Ensure middleware is registered first |
| Rate limiting not working | Check limiter is registered in `main.py` |

---

## File Path Examples

```
# ORM models
/backend/app/models/db_models.py

# API schemas (request/response)
/backend/app/models/schemas.py

# Endpoint implementations
/backend/app/routers/sessions.py
/backend/app/routers/patients.py

# Business logic
/backend/app/services/note_extraction.py

# Configuration
/backend/app/config.py

# Tests
/backend/tests/routers/test_sessions.py
/backend/tests/services/test_note_extraction.py

# Migrations
/backend/alembic/versions/b2c3d4e5f6g7_add_missing_user_columns.py
```

---

## For Treatment Plans Feature

You'll create/modify:

1. **New database model:**
   - `app/models/db_models.py` → `class TreatmentPlan(Base)`

2. **New API schemas:**
   - `app/models/schemas.py` → `TreatmentPlanCreate`, `TreatmentPlanResponse`

3. **New router:**
   - `app/routers/treatment_plans.py` → CRUD endpoints

4. **New service (optional):**
   - `app/services/treatment_plans.py` → Business logic

5. **New validators (optional):**
   - `app/validators.py` → `validate_treatment_goal()`

6. **New tests:**
   - `tests/routers/test_treatment_plans.py` → Full test coverage

7. **New migration:**
   - `alembic/versions/xxxxx_add_treatment_plans_table.py`

Then register in `main.py`:
```python
from app.routers import treatment_plans
app.include_router(treatment_plans.router, prefix="/api/treatment-plans")
```

