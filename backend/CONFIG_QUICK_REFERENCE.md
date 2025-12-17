# Configuration Quick Reference

## Import

```python
from app.config import settings
```

## Database

```python
settings.DATABASE_URL              # Original URL
settings.async_database_url        # postgresql+asyncpg://... (auto-converted)
settings.sync_database_url         # postgresql://... (auto-converted)
settings.DB_POOL_SIZE              # Default: 10
settings.DB_MAX_OVERFLOW           # Default: 20
settings.DB_POOL_TIMEOUT           # Default: 30
settings.SQL_ECHO                  # Default: False (MUST be False in prod)
```

## OpenAI

```python
settings.OPENAI_API_KEY.get_secret_value()  # SecretStr - call get_secret_value()
settings.OPENAI_MODEL              # Default: "gpt-4o"
settings.OPENAI_TIMEOUT            # Default: 120 seconds
settings.OPENAI_MAX_RETRIES        # Default: 3
settings.OPENAI_TEMPERATURE        # Default: 0.3
```

## Authentication (JWT)

```python
settings.JWT_SECRET_KEY            # Required, min 32 chars
settings.JWT_ALGORITHM             # Default: "HS256"
settings.ACCESS_TOKEN_EXPIRE_MINUTES   # Default: 30
settings.REFRESH_TOKEN_EXPIRE_DAYS     # Default: 7
```

## CORS

```python
settings.CORS_ORIGINS              # List[str], default: localhost:3000, localhost:5173
settings.CORS_CREDENTIALS          # Default: True
```

## File Uploads

```python
settings.UPLOAD_DIR                # Path, default: uploads/audio
settings.MAX_UPLOAD_SIZE_MB        # Default: 100
settings.max_upload_size_bytes     # Computed: MB * 1024 * 1024
settings.ALLOWED_AUDIO_FORMATS     # List[str], default: mp3,wav,m4a,ogg,flac
```

## Cleanup

```python
settings.FAILED_SESSION_RETENTION_DAYS      # Default: 7
settings.ORPHANED_FILE_RETENTION_HOURS      # Default: 24
settings.AUTO_CLEANUP_ON_STARTUP            # Default: False
settings.CLEANUP_SCHEDULE_HOUR              # Default: 3 (0-23)
```

## Rate Limiting

```python
settings.RATE_LIMIT_ENABLED        # Default: True
settings.RATE_LIMIT_LOGIN          # Default: "5/minute"
settings.RATE_LIMIT_SIGNUP         # Default: "3/hour"
settings.RATE_LIMIT_REFRESH        # Default: "10/minute"
settings.RATE_LIMIT_API            # Default: "100/minute"
```

## Server

```python
settings.HOST                      # Default: "0.0.0.0"
settings.PORT                      # Default: 8000
settings.WORKERS                   # Default: 1
```

## Environment

```python
settings.ENVIRONMENT               # Enum: development/staging/production
settings.DEBUG                     # Default: False (MUST be False in prod)
settings.LOG_LEVEL                 # Default: "INFO"

# Helpers
settings.is_production             # bool
settings.is_development            # bool
settings.is_staging                # bool
```

## Validation on Startup

```python
from app.config import validate_settings

# In main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()  # Prints config and validates
    yield
```

## Environment Variables (.env)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/db
OPENAI_API_KEY=sk-your-key-here

# Recommended for production
ENVIRONMENT=production
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>

# Optional (sensible defaults)
DEBUG=false
DB_POOL_SIZE=10
OPENAI_MODEL=gpt-4o
CORS_ORIGINS=https://app.example.com
```

## Production Security

Settings that **MUST be False** in production:
- `DEBUG=false`
- `SQL_ECHO=false`

Settings that **MUST be set** in production:
- `JWT_SECRET_KEY` (min 32 chars, use `openssl rand -hex 32`)
- `CORS_ORIGINS` (production URLs only, no localhost)

**Config validation will fail startup if these are violated.**

## Testing

```python
def test_with_custom_config(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/testdb")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    import importlib
    import app.config
    importlib.reload(app.config)

    from app.config import settings
    assert settings.DATABASE_URL == "postgresql://test@localhost/testdb"
```

## Backward Compatibility

Old auth_config still works:
```python
from app.auth.config import auth_config

auth_config.SECRET_KEY  # Proxies to settings.JWT_SECRET_KEY
```

But prefer:
```python
from app.config import settings

settings.JWT_SECRET_KEY
```
