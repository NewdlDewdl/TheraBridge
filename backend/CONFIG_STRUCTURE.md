# Configuration Structure Overview

## File Organization

```
backend/
├── app/
│   ├── config.py                    # 🎯 CENTRALIZED CONFIG (535 lines)
│   │   ├── Environment enum
│   │   ├── Settings class (Pydantic BaseSettings)
│   │   │   ├── Environment Configuration
│   │   │   ├── Database Configuration
│   │   │   ├── OpenAI API Configuration
│   │   │   ├── JWT Authentication Configuration
│   │   │   ├── CORS Configuration
│   │   │   ├── File Upload Configuration
│   │   │   ├── Cleanup Configuration
│   │   │   ├── Rate Limiting Configuration
│   │   │   ├── Server Configuration
│   │   │   └── Logging Configuration
│   │   ├── Validators (security, parsing, ranges)
│   │   ├── Computed properties (URL conversion, helpers)
│   │   ├── validate_settings() function
│   │   └── AuthConfig backward compatibility wrapper
│   │
│   └── auth/
│       └── config.py                # (Legacy, still works via wrapper)
│
├── tests/
│   └── test_config.py               # 🧪 TEST SUITE (320 lines)
│       ├── TestSettingsValidation
│       ├── TestSettingsParsing
│       ├── TestComputedProperties
│       ├── TestBackwardCompatibility
│       └── TestDefaultValues
│
├── .env.example                     # 📝 ENV TEMPLATE (124 lines)
│
├── CONFIG_MIGRATION_GUIDE.md        # 📚 MIGRATION GUIDE (392 lines)
│
├── CONFIG_QUICK_REFERENCE.md        # 🚀 QUICK REFERENCE (167 lines)
│
└── CONFIG_STRUCTURE.md              # 📊 THIS FILE
```

## Configuration Sections (10 Total)

### 1. Environment Configuration
**Purpose**: Control deployment environment and debug settings

```python
ENVIRONMENT: development | staging | production
DEBUG: bool (MUST be False in production)
LOG_LEVEL: DEBUG | INFO | WARNING | ERROR | CRITICAL
LOG_FORMAT: str
```

**Security**: Production enforces DEBUG=False

---

### 2. Database Configuration
**Purpose**: PostgreSQL connection and pool management

```python
DATABASE_URL: str (required)
DB_POOL_SIZE: int (default: 10)
DB_MAX_OVERFLOW: int (default: 20)
DB_POOL_TIMEOUT: int (default: 30)
SQL_ECHO: bool (MUST be False in production)

# Computed properties:
async_database_url: str (postgresql+asyncpg://...)
sync_database_url: str (postgresql://...)
```

**Security**: Production enforces SQL_ECHO=False (prevents PHI exposure)

---

### 3. OpenAI API Configuration
**Purpose**: GPT-4o note extraction settings

```python
OPENAI_API_KEY: SecretStr (required)
OPENAI_MODEL: str (default: "gpt-4o")
OPENAI_TIMEOUT: int (default: 120 seconds)
OPENAI_MAX_RETRIES: int (default: 3)
OPENAI_TEMPERATURE: float (default: 0.3)
```

**Note**: OPENAI_API_KEY is SecretStr (won't print in logs)

---

### 4. JWT Authentication Configuration
**Purpose**: Token generation and validation

```python
JWT_SECRET_KEY: str (required, min 32 chars)
JWT_ALGORITHM: str (default: "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int (default: 30)
REFRESH_TOKEN_EXPIRE_DAYS: int (default: 7)
```

**Security**: Production warns if JWT_SECRET_KEY looks like default

---

### 5. CORS Configuration
**Purpose**: Control which frontends can access API

```python
CORS_ORIGINS: List[str] (default: ["http://localhost:3000", "http://localhost:5173"])
CORS_CREDENTIALS: bool (default: True)
```

**Security**: Production warns if CORS_ORIGINS contains "localhost"

---

### 6. File Upload Configuration
**Purpose**: Audio file upload constraints

```python
UPLOAD_DIR: Path (default: uploads/audio)
MAX_UPLOAD_SIZE_MB: int (default: 100)
ALLOWED_AUDIO_FORMATS: List[str] (default: ["mp3", "wav", "m4a", "ogg", "flac"])

# Computed property:
max_upload_size_bytes: int (MB * 1024 * 1024)
```

**Note**: UPLOAD_DIR created automatically on startup

---

### 7. Cleanup Configuration
**Purpose**: Manage retention and cleanup of old files

```python
FAILED_SESSION_RETENTION_DAYS: int (default: 7)
ORPHANED_FILE_RETENTION_HOURS: int (default: 24)
AUTO_CLEANUP_ON_STARTUP: bool (default: False)
CLEANUP_SCHEDULE_HOUR: int (default: 3, range: 0-23)
```

**Note**: CLEANUP_SCHEDULE_HOUR reserved for future scheduled cleanup

---

### 8. Rate Limiting Configuration
**Purpose**: Prevent abuse and brute force attacks

```python
RATE_LIMIT_ENABLED: bool (default: True)
RATE_LIMIT_LOGIN: str (default: "5/minute")
RATE_LIMIT_SIGNUP: str (default: "3/hour")
RATE_LIMIT_REFRESH: str (default: "10/minute")
RATE_LIMIT_API: str (default: "100/minute")
```

**Format**: "count/period" where period is minute, hour, day

---

### 9. Server Configuration
**Purpose**: Uvicorn server settings

```python
HOST: str (default: "0.0.0.0")
PORT: int (default: 8000, range: 1-65535)
WORKERS: int (default: 1)
```

---

### 10. Logging Configuration
**Purpose**: Control logging verbosity and format

```python
LOG_LEVEL: str (default: "INFO")
LOG_FORMAT: str (default: timestamp + name + level + message)
```

---

## Validation Layers

### Layer 1: Pydantic Type Validation
- Automatically validates types (str, int, bool, List, Path, etc.)
- Converts environment variables to proper types
- Enforces required fields (marked with `...`)

### Layer 2: Field Validators
- Range validation (ge, le for integers)
- Length validation (min 32 chars for JWT_SECRET_KEY)
- Format validation (LOG_LEVEL must be valid Python level)
- Custom parsing (comma-separated strings to lists)

### Layer 3: Environment-Specific Validation (model_post_init)
- **Production only**:
  - Enforces DEBUG=False
  - Enforces SQL_ECHO=False
  - Warns if JWT_SECRET_KEY looks default
  - Warns if CORS_ORIGINS contains localhost

### Layer 4: Startup Validation (validate_settings)
- Prints configuration summary
- Verifies required fields are present
- Provides clear error messages
- Fails fast before handling any requests

---

## Security Features

### 1. Fail-Fast Validation
```python
# In main.py lifespan
from app.config import validate_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()  # Crash if config invalid
    yield
```

**Benefit**: Invalid config discovered on startup, not during production requests

### 2. Production Security Enforcement
```python
if settings.ENVIRONMENT == Environment.PRODUCTION:
    if settings.DEBUG:
        raise ValueError("DEBUG must be False in production")
    if settings.SQL_ECHO:
        raise ValueError("SQL_ECHO must be False in production")
```

**Benefit**: Cannot accidentally deploy with debug enabled (PHI exposure risk)

### 3. Secret Handling
```python
OPENAI_API_KEY: SecretStr  # Won't print in logs or __repr__

# Usage:
api_key = settings.OPENAI_API_KEY.get_secret_value()
```

**Benefit**: API keys don't leak in logs

### 4. Minimum Key Length
```python
@field_validator("JWT_SECRET_KEY")
def validate_jwt_secret(cls, v: str) -> str:
    if len(v) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
    return v
```

**Benefit**: Enforces strong secret keys

---

## Computed Properties

### Database URL Conversion
```python
@property
def async_database_url(self) -> str:
    """Convert postgres:// to postgresql+asyncpg:// and remove unsupported params"""
    # Handles: postgres://, postgresql://, sslmode, channel_binding
    return url

@property
def sync_database_url(self) -> str:
    """Convert to synchronous postgresql:// for auth operations"""
    return self.async_database_url.replace("postgresql+asyncpg://", "postgresql://")
```

### Environment Helpers
```python
@property
def is_production(self) -> bool:
    return self.ENVIRONMENT == Environment.PRODUCTION

@property
def is_development(self) -> bool:
    return self.ENVIRONMENT == Environment.DEVELOPMENT

@property
def is_staging(self) -> bool:
    return self.ENVIRONMENT == Environment.STAGING
```

### Unit Conversion
```python
@property
def max_upload_size_bytes(self) -> int:
    """Convert MAX_UPLOAD_SIZE_MB to bytes for FastAPI"""
    return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
```

---

## Backward Compatibility

### AuthConfig Wrapper
```python
class AuthConfig:
    """Backward compatibility for app/auth/config.py users"""
    @property
    def SECRET_KEY(self) -> str:
        return settings.JWT_SECRET_KEY

    @property
    def ALGORITHM(self) -> str:
        return settings.JWT_ALGORITHM

    # ... etc

auth_config = AuthConfig()
```

**Existing code continues to work:**
```python
from app.auth.config import auth_config
secret = auth_config.SECRET_KEY  # Still works!
```

**New code should use:**
```python
from app.config import settings
secret = settings.JWT_SECRET_KEY
```

---

## Usage Patterns

### 1. Single Import for All Config
```python
from app.config import settings

# Everything is available
database_url = settings.DATABASE_URL
api_key = settings.OPENAI_API_KEY.get_secret_value()
debug = settings.DEBUG
is_prod = settings.is_production
```

### 2. Startup Validation
```python
from app.config import validate_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()  # Print config + validate
    await init_db()
    yield
    await close_db()
```

### 3. Environment-Specific Logic
```python
from app.config import settings

if settings.is_production:
    # Production-only optimizations
    pool_size = settings.DB_POOL_SIZE * 2
else:
    # Development convenience
    pool_size = 5
```

### 4. Testing with Custom Config
```python
def test_feature(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/db")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    import importlib, app.config
    importlib.reload(app.config)

    from app.config import settings
    assert "test" in settings.DATABASE_URL
```

---

## File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| `app/config.py` | 535 | Core configuration module |
| `tests/test_config.py` | 320 | Comprehensive test suite |
| `CONFIG_MIGRATION_GUIDE.md` | 392 | Step-by-step migration instructions |
| `CONFIG_QUICK_REFERENCE.md` | 167 | Quick lookup reference |
| `.env.example` | 124 | Environment variable template |
| **TOTAL** | **1,538** | Complete configuration system |

---

## Benefits Summary

| Benefit | Before | After |
|---------|--------|-------|
| **Configuration Loading** | Scattered `load_dotenv()` calls | Single centralized module |
| **Type Safety** | `os.getenv()` returns `Optional[str]` | Pydantic validates to proper types |
| **Validation** | Runtime errors during requests | Fail-fast on startup |
| **Security** | No production checks | DEBUG/SQL_ECHO enforced in prod |
| **Documentation** | Scattered across files | All in one place with docstrings |
| **Testing** | Mock `os.getenv()` everywhere | Mock single `settings` object |
| **Defaults** | Hardcoded in code | Configurable via env vars |
| **Maintainability** | Change config in 10+ files | Change in one place |

---

## Quick Start

### 1. Installation
```bash
# Already included in requirements.txt
pip install pydantic-settings>=2.0.0
```

### 2. Create .env file
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Import and use
```python
from app.config import settings

# Type-safe, validated, with defaults
database_url = settings.DATABASE_URL
```

### 4. Validate on startup
```python
from app.config import validate_settings

validate_settings()  # Fail fast if anything wrong
```

**That's it! 🎉**
