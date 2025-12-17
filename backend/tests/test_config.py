"""
Tests for centralized configuration module.

These tests verify that:
1. All required settings are validated correctly
2. Environment-specific validation works (production security checks)
3. Default values are appropriate
4. Type coercion and parsing works (comma-separated lists, etc.)
5. Computed properties work correctly
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

# We'll need to reload the settings module for each test to test different configs
import importlib
import sys


class TestSettingsValidation:
    """Test configuration validation and security checks."""

    def test_missing_required_fields(self, monkeypatch):
        """Test that missing required fields raise ValidationError."""
        # Clear all environment variables
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Reload the settings module
        if "app.config" in sys.modules:
            importlib.reload(sys.modules["app.config"])
        else:
            import app.config

        # Attempt to create settings should fail
        with pytest.raises(ValidationError) as exc_info:
            from app.config import Settings
            Settings()

        # Should complain about missing required fields
        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "DATABASE_URL" in missing_fields
        assert "OPENAI_API_KEY" in missing_fields

    def test_production_debug_validation(self, monkeypatch):
        """Test that DEBUG=True in production raises error."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        with pytest.raises(ValueError, match="DEBUG must be False in production"):
            from app.config import Settings
            Settings()

    def test_production_sql_echo_validation(self, monkeypatch):
        """Test that SQL_ECHO=True in production raises error."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SQL_ECHO", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        with pytest.raises(ValueError, match="SQL_ECHO must be False in production"):
            from app.config import Settings
            Settings()

    def test_jwt_secret_key_length_validation(self, monkeypatch):
        """Test that short JWT_SECRET_KEY raises error."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("JWT_SECRET_KEY", "short")  # Too short

        with pytest.raises(ValidationError, match="at least 32 characters"):
            from app.config import Settings
            Settings()

    def test_valid_development_config(self, monkeypatch):
        """Test that valid development configuration works."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)

        from app.config import Settings
        settings = Settings()

        assert settings.ENVIRONMENT.value == "development"
        assert settings.DEBUG is True
        assert settings.is_development is True
        assert settings.is_production is False

    def test_valid_production_config(self, monkeypatch):
        """Test that valid production configuration works."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SQL_ECHO", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

        from app.config import Settings
        settings = Settings()

        assert settings.ENVIRONMENT.value == "production"
        assert settings.DEBUG is False
        assert settings.SQL_ECHO is False
        assert settings.is_production is True


class TestSettingsParsing:
    """Test parsing and type coercion of configuration values."""

    def test_cors_origins_from_string(self, monkeypatch):
        """Test parsing comma-separated CORS origins."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://app.example.com")

        from app.config import Settings
        settings = Settings()

        assert len(settings.CORS_ORIGINS) == 3
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "https://app.example.com" in settings.CORS_ORIGINS

    def test_allowed_audio_formats_from_string(self, monkeypatch):
        """Test parsing comma-separated audio formats."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("ALLOWED_AUDIO_FORMATS", "mp3, wav, flac")

        from app.config import Settings
        settings = Settings()

        assert len(settings.ALLOWED_AUDIO_FORMATS) == 3
        assert "mp3" in settings.ALLOWED_AUDIO_FORMATS
        assert "wav" in settings.ALLOWED_AUDIO_FORMATS
        assert "flac" in settings.ALLOWED_AUDIO_FORMATS

    def test_boolean_parsing(self, monkeypatch):
        """Test parsing boolean values from environment."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SQL_ECHO", "1")
        monkeypatch.setenv("CORS_CREDENTIALS", "yes")

        from app.config import Settings
        settings = Settings()

        assert settings.DEBUG is True
        assert settings.SQL_ECHO is True
        assert settings.CORS_CREDENTIALS is True

    def test_integer_range_validation(self, monkeypatch):
        """Test that integer fields respect min/max constraints."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("PORT", "999999")  # Out of range

        with pytest.raises(ValidationError):
            from app.config import Settings
            Settings()

    def test_log_level_validation(self, monkeypatch):
        """Test that LOG_LEVEL only accepts valid values."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError, match="LOG_LEVEL must be one of"):
            from app.config import Settings
            Settings()


class TestComputedProperties:
    """Test computed properties and derived values."""

    def test_async_database_url(self, monkeypatch):
        """Test async database URL conversion."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db?sslmode=require")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        from app.config import Settings
        settings = Settings()

        async_url = settings.async_database_url
        assert "postgresql+asyncpg://" in async_url
        assert "sslmode" not in async_url  # Should be removed

    def test_sync_database_url(self, monkeypatch):
        """Test sync database URL conversion."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        from app.config import Settings
        settings = Settings()

        sync_url = settings.sync_database_url
        assert sync_url.startswith("postgresql://")
        assert "asyncpg" not in sync_url

    def test_max_upload_size_bytes(self, monkeypatch):
        """Test conversion of MB to bytes."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "50")

        from app.config import Settings
        settings = Settings()

        assert settings.max_upload_size_bytes == 50 * 1024 * 1024

    def test_environment_helpers(self, monkeypatch):
        """Test is_production, is_development, is_staging helpers."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        # Test development
        monkeypatch.setenv("ENVIRONMENT", "development")
        from app.config import Settings
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_staging is False

        # Test production (need to reload)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        if "app.config" in sys.modules:
            importlib.reload(sys.modules["app.config"])
        from app.config import Settings
        settings = Settings()
        assert settings.is_production is True
        assert settings.is_development is False


class TestBackwardCompatibility:
    """Test backward compatibility with auth_config."""

    def test_auth_config_wrapper(self, monkeypatch):
        """Test that auth_config wrapper provides same values as settings."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("JWT_ALGORITHM", "HS256")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "14")

        from app.config import settings, auth_config

        assert auth_config.SECRET_KEY == settings.JWT_SECRET_KEY
        assert auth_config.ALGORITHM == settings.JWT_ALGORITHM
        assert auth_config.ACCESS_TOKEN_EXPIRE_MINUTES == settings.ACCESS_TOKEN_EXPIRE_MINUTES
        assert auth_config.REFRESH_TOKEN_EXPIRE_DAYS == settings.REFRESH_TOKEN_EXPIRE_DAYS


class TestDefaultValues:
    """Test that default values are appropriate."""

    def test_default_values(self, monkeypatch):
        """Test that all defaults are set correctly."""
        # Only set required fields
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")

        from app.config import Settings
        settings = Settings()

        # Environment defaults
        assert settings.ENVIRONMENT.value == "development"
        assert settings.DEBUG is False

        # Database defaults
        assert settings.DB_POOL_SIZE == 10
        assert settings.DB_MAX_OVERFLOW == 20
        assert settings.DB_POOL_TIMEOUT == 30
        assert settings.SQL_ECHO is False

        # OpenAI defaults
        assert settings.OPENAI_MODEL == "gpt-4o"
        assert settings.OPENAI_TIMEOUT == 120
        assert settings.OPENAI_MAX_RETRIES == 3
        assert settings.OPENAI_TEMPERATURE == 0.3

        # JWT defaults
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

        # CORS defaults
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert settings.CORS_CREDENTIALS is True

        # Upload defaults
        assert settings.UPLOAD_DIR == Path("uploads/audio")
        assert settings.MAX_UPLOAD_SIZE_MB == 100
        assert "mp3" in settings.ALLOWED_AUDIO_FORMATS

        # Rate limit defaults
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_LOGIN == "5/minute"

        # Server defaults
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.WORKERS == 1

        # Log defaults
        assert settings.LOG_LEVEL == "INFO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
