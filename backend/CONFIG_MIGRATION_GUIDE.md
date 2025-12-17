# Configuration Migration Guide

## Overview

This guide explains how to migrate from scattered environment variable loading to the centralized `app/config.py` module.

## What Changed

### Before (Problems)
- Multiple `load_dotenv()` calls with inconsistent paths
- Environment variables accessed via `os.getenv()` throughout codebase
- No validation - errors only discovered at runtime
- No environment-specific security checks
- Hardcoded configuration values (CORS origins, OpenAI model, etc.)

### After (Benefits)
- **Single source of truth**: All configuration in `app/config.py`
- **Type safety**: Pydantic validates types and constraints
- **Fail fast**: Invalid configuration detected on startup, not during requests
- **Environment profiles**: development/staging/production with specific validation
- **Security checks**: Production validates DEBUG=false, SQL_ECHO=false, etc.
- **Easy testing**: Mock configuration by patching `settings` object

## Migration Steps

### 1. Import the new settings module

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

**After:**
```python
from app.config import settings

# Use settings.DATABASE_URL
```

### 2. Update environment variable access

**Before:**
```python
api_key = os.getenv("OPENAI_API_KEY")
debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
cors_origins = ["http://localhost:3000", "http://localhost:5173"]
```

**After:**
```python
from app.config import settings

api_key = settings.OPENAI_API_KEY.get_secret_value()  # SecretStr type
debug = settings.DEBUG  # Already a bool
cors_origins = settings.CORS_ORIGINS  # Already a list
```

### 3. Remove load_dotenv() calls

**Files to update:**
- `app/main.py` - Remove `load_dotenv()`
- `app/database.py` - Remove `load_dotenv("../audio-transcription-pipeline/.env")`
- `app/services/note_extraction.py` - Remove `load_dotenv("../audio-transcription-pipeline/.env")`

**The centralized config module handles .env loading automatically.**

### 4. Update database.py

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv("../audio-transcription-pipeline/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes")

# Convert postgres:// to postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
```

**After:**
```python
from app.config import settings

# All conversion and validation handled by settings
engine = create_async_engine(
    settings.async_database_url,  # Already converted to asyncpg
    echo=settings.SQL_ECHO,       # Already a bool
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    connect_args={"ssl": "require"}
)

# For sync operations
sync_engine = create_engine(
    settings.sync_database_url,  # Already converted to psycopg
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)
```

### 5. Update main.py

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

app = FastAPI(debug=DEBUG_MODE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After:**
```python
from app.config import settings, validate_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Validate configuration on startup
    validate_settings()

    await init_db()
    yield
    await close_db()

app = FastAPI(
    title="TherapyBridge API",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG  # Type-safe boolean
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # From config
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. Update note_extraction.py

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv("../audio-transcription-pipeline/.env")

class NoteExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
```

**After:**
```python
from app.config import settings

class NoteExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        # Use settings as default, allow override for testing
        self.api_key = api_key or settings.OPENAI_API_KEY.get_secret_value()

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES
        )
        self.model = settings.OPENAI_MODEL  # Configurable via env
```

### 7. Update auth configuration

The existing `app/auth/config.py` uses Pydantic BaseSettings but loads a subset of config. The new centralized config includes all auth settings and provides a **backward compatibility wrapper**.

**Existing code using auth_config continues to work:**
```python
from app.auth.config import auth_config

# These still work (they proxy to centralized settings)
secret = auth_config.SECRET_KEY
algorithm = auth_config.ALGORITHM
expire_minutes = auth_config.ACCESS_TOKEN_EXPIRE_MINUTES
```

**New code should use centralized settings:**
```python
from app.config import settings

secret = settings.JWT_SECRET_KEY
algorithm = settings.JWT_ALGORITHM
expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
```

**Eventually deprecate `app/auth/config.py`** and replace all imports with `app.config`.

### 8. Update .env file

Your `.env` file should match the structure in `.env.example`. Key changes:

```bash
# NEW: Environment profile
ENVIRONMENT=development

# Existing settings work as before
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
DEBUG=false

# NEW: Optional settings with good defaults
DB_POOL_SIZE=10
OPENAI_TIMEOUT=120
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Testing

### Test configuration loading

```python
from app.config import settings

# Validate on startup (call this in main.py lifespan)
from app.config import validate_settings
validate_settings()
```

### Test with custom environment

```python
import pytest

def test_with_custom_config(monkeypatch):
    """Test with custom environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/testdb")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    # Reload config
    import importlib
    import app.config
    importlib.reload(app.config)

    from app.config import settings
    assert "testdb" in settings.DATABASE_URL
```

## Environment-Specific Configuration

### Development
```bash
ENVIRONMENT=development
DEBUG=true                        # Allowed in dev
SQL_ECHO=true                     # Allowed in dev
CORS_ORIGINS=http://localhost:3000
```

### Staging
```bash
ENVIRONMENT=staging
DEBUG=false                       # Required
SQL_ECHO=false                    # Required
CORS_ORIGINS=https://staging.example.com
```

### Production
```bash
ENVIRONMENT=production
DEBUG=false                       # STRICTLY ENFORCED
SQL_ECHO=false                    # STRICTLY ENFORCED
JWT_SECRET_KEY=<strong-random-key>  # CRITICAL
CORS_ORIGINS=https://app.example.com
```

**Production will fail to start if:**
- `DEBUG=true`
- `SQL_ECHO=true`
- `JWT_SECRET_KEY` is too short (<32 chars)
- CORS_ORIGINS contains "localhost" (warning only)

## Common Patterns

### Accessing secret values

```python
# OPENAI_API_KEY is a SecretStr (doesn't print in logs)
api_key = settings.OPENAI_API_KEY.get_secret_value()
```

### Accessing computed properties

```python
# Database URLs (automatically converted)
async_url = settings.async_database_url  # postgresql+asyncpg://...
sync_url = settings.sync_database_url    # postgresql://...

# File size in bytes
max_bytes = settings.max_upload_size_bytes  # 100MB -> 104857600 bytes

# Environment checks
if settings.is_production:
    # Production-only logic
    pass
```

### Adding new configuration

1. Add field to `Settings` class in `app/config.py`
2. Add default value or mark as required (`...`)
3. Add to `.env.example` with documentation
4. Add validator if needed (e.g., range check, format validation)
5. Add tests in `tests/test_config.py`

Example:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    NEW_FEATURE_ENABLED: bool = Field(
        default=False,
        description="Enable new experimental feature"
    )

    @field_validator("NEW_FEATURE_ENABLED")
    @classmethod
    def validate_new_feature(cls, v: bool, info) -> bool:
        """Prevent enabling in production without explicit approval."""
        # Custom validation logic
        return v
```

## Rollback Plan

If issues arise during migration:

1. **Keep old code temporarily**: Comment out new imports, restore old code
2. **Gradual migration**: Migrate one module at a time, test thoroughly
3. **Feature flag**: Add `USE_CENTRALIZED_CONFIG` env var to toggle behavior

## Checklist

- [ ] Update `app/main.py` to import from `app.config`
- [ ] Update `app/database.py` to use `settings.async_database_url`
- [ ] Update `app/services/note_extraction.py` to use `settings.OPENAI_*`
- [ ] Remove all `load_dotenv()` calls except in `app/config.py`
- [ ] Remove all `os.getenv()` calls, replace with `settings.*`
- [ ] Update `.env` file to match `.env.example` structure
- [ ] Add `validate_settings()` call to startup lifespan
- [ ] Run tests: `pytest tests/test_config.py -v`
- [ ] Test production deployment with `ENVIRONMENT=production`
- [ ] Update deployment docs with new env vars
- [ ] Deprecate `app/auth/config.py` (optional, backward compat exists)

## Benefits Summary

1. **Type Safety**: Pydantic validates all config at startup
2. **Fail Fast**: Bad config crashes on startup, not during requests
3. **Security**: Production enforces DEBUG=false, SQL_ECHO=false
4. **Documentation**: All config in one place with docstrings
5. **Testability**: Easy to mock `settings` for tests
6. **Maintainability**: Add/change config in one file
7. **Environment Profiles**: Different validation for dev/staging/prod
