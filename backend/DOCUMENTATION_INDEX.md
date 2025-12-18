# Backend Documentation Index

This directory contains comprehensive documentation of the TherapyBridge backend architecture and implementation patterns.

## Documentation Files

### 1. BACKEND_STRUCTURE_ANALYSIS.md (26 KB)
**Best for:** Understanding every detail of how the backend works

**Contents:**
- Complete project overview with tech stack
- Full directory structure explanation
- Core organization patterns and separation of concerns
- **File-by-file guide** with code examples for:
  - database.py - Database connection and pooling
  - config.py - Configuration management
  - db_models.py - Database models
  - schemas.py - API request/response validation
  - validators.py - Input validation utilities
  - Routers (sessions, patients, analytics)
  - Services (note extraction, transcription)
  - Middleware (rate limiting, error handling, correlation ID)
  - main.py - App initialization
  - Authentication module
- Import patterns and dependency injection
- Configuration hierarchy
- Testing structure and patterns
- Design patterns used throughout
- **Key conventions for new features** (Treatment Plans example)

**Read this when:**
- You need to understand a specific component deeply
- You're implementing a new feature and want to see similar examples
- You want to understand the design decisions
- You need to know how something works internally

---

### 2. ARCHITECTURE_QUICK_REFERENCE.md (7.6 KB)
**Best for:** Quick lookup and common operations

**Contents:**
- Request flow diagram (at-a-glance)
- Key files and their roles (quick table)
- Data flow example with step-by-step breakdown
- Testing organization overview
- Common operations with code snippets:
  - Add a new endpoint
  - Add a database model
  - Call external APIs
  - Validate user input
- Database relationships explained
- Async/await patterns
- Configuration loading order
- Error handling levels
- Security notes
- Common gotchas and solutions
- File path reference table
- Treatment Plans feature implementation guide

**Read this when:**
- You need a quick answer to "how do I do X?"
- You're implementing a feature and need patterns
- You're debugging an issue
- You need to remember a specific file location

---

### 3. PROJECT_STRUCTURE_VISUAL.md (21 KB)
**Best for:** Visual learners and quick navigation

**Contents:**
- Complete directory tree with emoji indicators
  - Shows all folders and key files
  - Describes purpose of each file/folder
  - Color-coded by type
- Data model relationships diagram
  - Shows all tables and their connections
  - Visualizes foreign key relationships
  - Shows cascade behavior
- Request processing pipeline (ASCII flow diagram)
  - HTTP request → Response
  - Shows middleware chain
  - Shows dependency injection
  - Shows validation → business logic → database
- Key patterns at a glance
  - Async/Await
  - Dependency Injection
  - Schema Layering
  - Error Handling
- File naming conventions for each folder
- Async operations timeline
- Quick file location reference (table)

**Read this when:**
- You want to understand the overall structure visually
- You're trying to find a file
- You want to understand data relationships
- You need to see how requests flow through the system

---

## How to Use This Documentation

### Scenario 1: Adding Treatment Plans Feature
1. Start with **ARCHITECTURE_QUICK_REFERENCE.md** - "For Treatment Plans Feature" section
2. Read **BACKEND_STRUCTURE_ANALYSIS.md** - Section 8 for detailed patterns
3. Use **PROJECT_STRUCTURE_VISUAL.md** - File location reference table

### Scenario 2: Implementing a New Endpoint
1. Reference **ARCHITECTURE_QUICK_REFERENCE.md** - "Add a New Endpoint" section
2. Look at **BACKEND_STRUCTURE_ANALYSIS.md** - Section 3.6 "Routers"
3. Use **PROJECT_STRUCTURE_VISUAL.md** - to find existing examples

### Scenario 3: Understanding the Data Model
1. View **PROJECT_STRUCTURE_VISUAL.md** - "Data Model Relationships Diagram"
2. Read **BACKEND_STRUCTURE_ANALYSIS.md** - Section 3.3 "ORM Models"
3. Check actual code in `/app/models/db_models.py`

### Scenario 4: Debugging a Request
1. Check **PROJECT_STRUCTURE_VISUAL.md** - "Request Processing Pipeline"
2. Review **ARCHITECTURE_QUICK_REFERENCE.md** - error handling section
3. Search **BACKEND_STRUCTURE_ANALYSIS.md** - for the specific component

### Scenario 5: Setting Up New Configuration
1. Read **ARCHITECTURE_QUICK_REFERENCE.md** - "Configuration Loading Order"
2. Review **BACKEND_STRUCTURE_ANALYSIS.md** - Section 3.2 "Configuration Module"
3. Check `/app/config.py` for actual implementation

---

## Quick Reference: File Locations

### Database Models
- Location: `/app/models/db_models.py`
- Contains: User, Patient, TherapistPatient, TherapySession, AuthSession

### API Schemas
- Location: `/app/models/schemas.py`
- Contains: All request/response schemas and enums

### Routers (Endpoints)
- Sessions: `/app/routers/sessions.py`
- Patients: `/app/routers/patients.py`
- Analytics: `/app/routers/analytics.py`
- Authentication: `/app/auth/router.py`
- Cleanup: `/app/routers/cleanup.py`

### Services (Business Logic)
- Note Extraction: `/app/services/note_extraction.py`
- Transcription: `/app/services/transcription.py`
- Analytics: `/app/services/analytics.py`
- Cleanup: `/app/services/cleanup.py`

### Configuration
- Main Config: `/app/config.py`
- Database: `/app/database.py`
- Validators: `/app/validators.py`

### Middleware
- Rate Limiting: `/app/middleware/rate_limit.py`
- Error Handling: `/app/middleware/error_handler.py`
- Correlation ID: `/app/middleware/correlation_id.py`

### Application Entry Point
- Main App: `/app/main.py`
- Auth Module: `/app/auth/router.py`

### Tests
- Router Tests: `/tests/routers/test_*.py`
- Service Tests: `/tests/services/test_*.py`
- Integration Tests: `/tests/test_auth_integration.py`
- Fixtures: `/tests/conftest.py`

### Migrations
- Migration Scripts: `/alembic/versions/`
- Migration Config: `/alembic.ini`

---

## Architecture Summary

```
Request
  ↓
Middleware (Rate limit, CORS, Error handling, Correlation ID)
  ↓
Route Handler (routers/*.py)
  ↓
Dependency Injection (get_db, get_current_user)
  ↓
Input Validation (Pydantic schemas + validators.py)
  ↓
Business Logic (services/*.py)
  ↓
Database Operations (db_models.py + SQLAlchemy)
  ↓
Response Serialization (schemas.py)
  ↓
HTTP Response
```

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | Async web framework |
| Database | PostgreSQL | Persistent data storage |
| ORM | SQLAlchemy 2.0+ | Database object mapping |
| Validation | Pydantic | Input/output validation |
| Authentication | JWT | User authentication |
| Password Hashing | bcrypt | Secure password storage |
| Migrations | Alembic | Database schema versioning |
| Testing | pytest | Unit/integration testing |
| Rate Limiting | slowapi | API rate limiting |
| Async Driver | asyncpg | PostgreSQL async driver |

---

## Common Patterns

### Dependency Injection
```python
async def endpoint(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Dependencies automatically provided
```

### Schema Validation
```python
class ItemCreate(BaseModel):
    name: str
    description: Optional[str]

@router.post("/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # Pydantic validates and converts automatically
```

### Database Query
```python
result = await db.execute(select(Item).where(Item.id == item_id))
item = result.scalar_one()
```

### Error Handling
```python
raise HTTPException(status_code=400, detail="Invalid input")
```

---

## Security Checklist

- [ ] Always validate input (use Pydantic or validators.py)
- [ ] Check authentication (use get_current_user dependency)
- [ ] Use SQLAlchemy ORM (prevents SQL injection)
- [ ] Hash passwords (bcrypt, never plain text)
- [ ] Rate limit auth endpoints
- [ ] Disable DEBUG in production
- [ ] Disable SQL_ECHO in production
- [ ] Use HTTPS (SSL enforced)
- [ ] Validate JWT signatures
- [ ] Log with correlation IDs (no PHI)

---

## For More Information

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Pydantic Documentation:** https://docs.pydantic.dev/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **Alembic Documentation:** https://alembic.sqlalchemy.org/

---

## Questions Answered by Each Document

### BACKEND_STRUCTURE_ANALYSIS.md answers:
- What is the complete structure of the backend?
- What does each file do in detail?
- What patterns are used and why?
- How do I add a new feature?
- What are the design principles?
- How are components organized?

### ARCHITECTURE_QUICK_REFERENCE.md answers:
- How do I add a new endpoint?
- Where do I put validation code?
- How do I call the database?
- How do I authenticate users?
- What are common errors and solutions?
- Where is the X file located?

### PROJECT_STRUCTURE_VISUAL.md answers:
- What files exist and what do they contain?
- How are data models related?
- What does a request flow look like?
- Where is the Y folder?
- What naming conventions are used?
- Can you show me a diagram?

---

## Document Locations

All documentation files are in the backend root directory:

```
/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/
├── DOCUMENTATION_INDEX.md              ← You are here
├── BACKEND_STRUCTURE_ANALYSIS.md       ← Detailed reference
├── ARCHITECTURE_QUICK_REFERENCE.md     ← Quick lookup
└── PROJECT_STRUCTURE_VISUAL.md         ← Visual guide
```

