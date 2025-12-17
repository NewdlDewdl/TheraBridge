# Backend Services - Concrete Improvement Examples

## Current Problems & Solutions

### Problem 1: Blocking Sync Client in Async Context

**CURRENT CODE (PROBLEMATIC):**
```python
# backend/app/services/note_extraction.py, line 91-92
from openai import OpenAI  # <-- SYNC CLIENT!

self.client = OpenAI(api_key=self.api_key)

# Line 113-127
response = self.client.chat.completions.create(  # <-- BLOCKS EVENT LOOP!
    model=self.model,
    messages=[...],
    temperature=0.3,
    response_format={"type": "json_object"}
)
```

**ISSUE:**
- `OpenAI()` is synchronous
- `.chat.completions.create()` blocks for 30-60 seconds
- Entire FastAPI event loop becomes unresponsive
- Only 1 request can be processed at a time (huge bottleneck)

**SOLUTION:**
```python
# backend/app/services/note_extraction.py (IMPROVED)
from openai import AsyncOpenAI  # <-- ASYNC CLIENT!

class NoteExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = AsyncOpenAI(api_key=self.api_key)  # <-- ASYNC!
        self.model = "gpt-4o"

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[list[TranscriptSegment]] = None
    ) -> ExtractedNotes:
        """Extract structured clinical notes from a therapy session transcript."""
        print(f"[NoteExtraction] Starting extraction for {len(transcript)} character transcript")
        start_time = time.time()

        # Call OpenAI API - NOW WITH AWAIT!
        response = await self.client.chat.completions.create(  # <-- AWAIT!
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical psychology expert who extracts structured data from therapy transcripts. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(transcript=transcript)
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # ... rest of method unchanged ...
```

**BENEFITS:**
- Event loop remains responsive (can handle multiple requests)
- ~100x improvement in server concurrency
- Still waits for API response (duration same), but doesn't block others
- Drop-in replacement (API is identical to sync version)

---

### Problem 2: Global Mutable Singleton (Anti-pattern)

**CURRENT CODE (PROBLEMATIC):**
```python
# backend/app/services/note_extraction.py, line 178-187
_extraction_service: Optional[NoteExtractionService] = None

def get_extraction_service() -> NoteExtractionService:
    """Get or create the extraction service singleton"""
    global _extraction_service  # <-- GLOBAL STATE!
    if _extraction_service is None:
        _extraction_service = NoteExtractionService()
    return _extraction_service

# Usage in router
extraction_service = get_extraction_service()  # <-- Hidden dependency!
```

**ISSUES:**
- Global mutable state (threading issue)
- Hidden dependency (hard to understand what's needed)
- Impossible to test with different configs
- Tightly coupled to environment variables

**SOLUTION - OPTION A: FastAPI Depends Pattern**
```python
# backend/app/config.py (NEW FILE)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# backend/app/services/__init__.py (UPDATED)
from app.config import settings
from app.services.note_extraction import NoteExtractionService

def get_extraction_service() -> NoteExtractionService:
    """Create extraction service (FastAPI will inject via Depends)"""
    return NoteExtractionService(api_key=settings.openai_api_key)

# backend/app/routers/sessions.py (UPDATED)
from fastapi import Depends
from app.services import get_extraction_service

@router.post("/{session_id}/extract-notes")
async def manually_extract_notes(
    session_id: UUID,
    extraction_service: NoteExtractionService = Depends(get_extraction_service),  # <-- INJECTED!
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger note extraction"""
    notes = await extraction_service.extract_notes_from_transcript(...)
    return ExtractNotesResponse(extracted_notes=notes, processing_time=...)
```

**SOLUTION - OPTION B: Direct Dependency Injection**
```python
# backend/app/main.py (UPDATED)
from contextlib import asynccontextmanager
from app.config import settings
from app.services.note_extraction import NoteExtractionService
from app.services.transcription import TranscriptionService

class ServiceContainer:
    def __init__(self, config: Settings):
        self.extraction = NoteExtractionService(api_key=config.openai_api_key)
        self.transcription = TranscriptionService(pipeline_dir=config.pipeline_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup - Create services once
    app.state.services = ServiceContainer(settings)
    print("✅ Services initialized")
    yield
    # Shutdown
    print("👋 Shutting down services")

# Create app with service container
app = FastAPI(
    title="TherapyBridge API",
    lifespan=lifespan
)

# Usage in routers
from fastapi import Request

@router.post("/extract-notes")
async def extract(request: Request, session_id: UUID):
    extraction_service = request.app.state.services.extraction
    notes = await extraction_service.extract_notes_from_transcript(...)
```

**BENEFITS:**
- Explicit dependencies (testable)
- Can easily swap implementations
- No global state
- Per-request or per-app lifecycle control

---

### Problem 3: No Error Handling in Background Tasks

**CURRENT CODE (PROBLEMATIC):**
```python
# backend/app/routers/sessions.py, line 31-116
async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """Background task to process audio: transcribe → extract notes"""
    try:
        # Update status: transcribing
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()

        # Step 1: Transcribe audio
        print(f"[Pipeline] Transcribing session {session_id}...")
        transcript_result = await transcribe_audio_file(audio_path)
        # ^ NO ERROR HANDLING! What if this fails?

        # Save transcript to database
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(...)
        )
        await db.commit()

        # Step 2: Extract notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.extracting_notes.value)
        )
        await db.commit()

        print(f"[Pipeline] Extracting notes for session {session_id}...")
        extraction_service = get_extraction_service()
        notes = await extraction_service.extract_notes_from_transcript(...)
        # ^ NO TIMEOUT! What if OpenAI hangs?

        # ... save to db ...

    except Exception as e:  # <-- TOO BROAD!
        print(f"[Pipeline] Error processing session {session_id}: {str(e)}")
        # ^ Just prints! No logging, no retry, no details
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()
```

**ISSUES:**
- Catches all exceptions (hides bugs)
- No retry logic
- No timeout on long-running operations
- Error messages too vague
- No structured logging
- Silent failures possible

**SOLUTION:**
```python
# backend/app/services/base.py (NEW FILE)
import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class TransientError(ServiceError):
    """Errors that might succeed if retried"""
    pass

class PermanentError(ServiceError):
    """Errors that won't succeed if retried"""
    pass

def with_timeout(seconds: int = 30):
    """Decorator to add timeout to async functions"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {seconds}s")
                raise TransientError(f"Operation timed out after {seconds}s")
        return wrapper
    return decorator

def with_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator to add retry logic to async functions"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except TransientError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
                except PermanentError:
                    raise
            raise last_exception or ServiceError("Unknown error")
        return wrapper
    return decorator

# backend/app/services/note_extraction.py (UPDATED)
from app.services.base import with_timeout, with_retry, TransientError

class NoteExtractionService:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 60, retries: int = 3):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
        self.timeout = timeout
        self.retries = retries

    @with_timeout(seconds=60)  # <-- TIMEOUT!
    @with_retry(max_retries=3)  # <-- RETRY!
    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[list[TranscriptSegment]] = None
    ) -> ExtractedNotes:
        """Extract structured clinical notes from a therapy session transcript."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[...],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise TransientError(f"Rate limited: {e}")
            elif "timeout" in str(e).lower():
                raise TransientError(f"API timeout: {e}")
            else:
                raise PermanentError(f"API error: {e}")
        
        # ... rest of method ...

# backend/app/routers/sessions.py (UPDATED)
import logging

logger = logging.getLogger(__name__)

async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """Background task to process audio: transcribe → extract notes"""
    logger.info(f"Starting pipeline for session {session_id}")
    
    try:
        # Update status: transcribing
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()

        # Step 1: Transcribe audio (with error handling)
        try:
            logger.info(f"Transcribing audio for session {session_id}")
            transcript_result = await transcribe_audio_file(audio_path, timeout=300)
        except TimeoutError as e:
            logger.error(f"Transcription timeout for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Transcription failed for session {session_id}: {e}", exc_info=True)
            raise

        # Save transcript
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                transcript_text=transcript_result["full_text"],
                transcript_segments=transcript_result["segments"],
                duration_seconds=int(transcript_result.get("duration", 0)),
                status=SessionStatus.transcribed.value
            )
        )
        await db.commit()

        # Step 2: Extract notes (with error handling)
        try:
            logger.info(f"Extracting notes for session {session_id}")
            extraction_service = get_extraction_service()
            notes = await extraction_service.extract_notes_from_transcript(
                transcript=transcript_result["full_text"],
                segments=transcript_result.get("segments")
            )
        except TransientError as e:
            logger.warning(f"Note extraction transient error for session {session_id}: {e}")
            # Could retry with manual trigger
            raise
        except PermanentError as e:
            logger.error(f"Note extraction failed for session {session_id}: {e}", exc_info=True)
            raise

        # Save notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                extracted_notes=notes.model_dump(),
                therapist_summary=notes.therapist_notes,
                patient_summary=notes.patient_summary,
                risk_flags=[flag.model_dump() for flag in notes.risk_flags],
                status=SessionStatus.processed.value,
                processed_at=datetime.utcnow()
            )
        )
        await db.commit()

        logger.info(f"Pipeline completed successfully for session {session_id}")

        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)

    except TransientError as e:
        logger.error(f"Pipeline transient error for session {session_id}: {e}")
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=f"Transient error (can retry): {str(e)}"
            )
        )
        await db.commit()

    except PermanentError as e:
        logger.error(f"Pipeline permanent error for session {session_id}: {e}")
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=f"Permanent error: {str(e)}"
            )
        )
        await db.commit()

    except Exception as e:
        logger.critical(f"Unexpected error in pipeline for session {session_id}: {e}", exc_info=True)
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=f"Unexpected error: {type(e).__name__}: {str(e)}"
            )
        )
        await db.commit()
```

**BENEFITS:**
- Specific exception types (TransientError vs PermanentError)
- Automatic retry with exponential backoff
- Timeout protection (won't hang forever)
- Structured logging (easy to debug)
- Distinguishes between recoverable and permanent failures

---

### Problem 4: Scattered Environment Loading

**CURRENT CODE (PROBLEMATIC):**
```python
# backend/app/database.py, line 12
load_dotenv("../audio-transcription-pipeline/.env")

# backend/app/services/note_extraction.py, line 12
load_dotenv("../audio-transcription-pipeline/.env")
# ^ LOADING SAME FILE TWICE!

# backend/app/services/transcription.py, line 9
PIPELINE_DIR = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline"
sys.path.insert(0, str(PIPELINE_DIR))
# ^ Different way to reference same path
```

**SOLUTION:**
```python
# backend/app/config.py (NEW FILE)
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_timeout: int = 60
    openai_retries: int = 3
    
    # Audio Pipeline
    pipeline_dir: Path = Path(__file__).parent.parent / "audio-transcription-pipeline"
    
    # Logging
    log_level: str = "INFO"
    
    # Feature flags
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def pipeline_path(self) -> str:
        """Get pipeline directory path"""
        return str(self.pipeline_dir)

# Load once at module level
settings = Settings()

# backend/app/main.py (UPDATED)
from app.config import settings
import logging

# Configure logging once
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print(f"🚀 Starting TherapyBridge API (debug={settings.debug_mode})")
    await init_db()
    print("✅ Database initialized")
    print(f"✅ Pipeline dir: {settings.pipeline_path}")
    print(f"✅ OpenAI timeout: {settings.openai_timeout}s, retries: {settings.openai_retries}")
    
    yield
    
    print("👋 Shutting down TherapyBridge API...")
    await close_db()
    print("✅ Database connections closed")

# backend/app/database.py (UPDATED)
from app.config import settings
# ^ Remove: load_dotenv("../audio-transcription-pipeline/.env")

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

# ... rest of file ...

# backend/app/services/note_extraction.py (UPDATED)
from app.config import settings
# ^ Remove: load_dotenv("../audio-transcription-pipeline/.env")

class NoteExtractionService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.openai_model,
        timeout: int = settings.openai_timeout,
        retries: int = settings.openai_retries
    ):
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.timeout = timeout
        self.retries = retries

# backend/app/services/transcription.py (UPDATED)
from app.config import settings

PIPELINE_DIR = settings.pipeline_dir  # ^ From config, not hardcoded!
sys.path.insert(0, str(PIPELINE_DIR))

from src.pipeline import AudioTranscriptionPipeline
```

**BENEFITS:**
- Single source of truth for configuration
- No scattered load_dotenv() calls
- Type-safe config (Pydantic validates)
- Easy to override for testing
- Clear defaults
- Centralized environment requirements

---

## Testing Example

```python
# backend/tests/test_services/test_note_extraction.py

import pytest
from unittest.mock import AsyncMock, patch
from app.services.note_extraction import NoteExtractionService
from app.models.schemas import ExtractedNotes

@pytest.mark.asyncio
async def test_extract_notes_success():
    """Test successful note extraction"""
    service = NoteExtractionService(api_key="test-key-123")
    
    # Mock OpenAI response
    mock_response = {
        "key_topics": ["anxiety", "coping strategies"],
        "topic_summary": "Session focused on anxiety management.",
        "strategies": [],
        "emotional_themes": ["anxious", "hopeful"],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "positive",
        "mood_trajectory": "improving",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Good session.",
        "patient_summary": "You discussed anxiety."
    }
    
    with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value.choices[0].message.content = json.dumps(mock_response)
        
        result = await service.extract_notes_from_transcript("Sample transcript")
        
        assert isinstance(result, ExtractedNotes)
        assert result.session_mood.value == "positive"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_extract_notes_timeout():
    """Test timeout handling"""
    service = NoteExtractionService(api_key="test-key-123")
    
    with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(TransientError, match="timed out"):
            await service.extract_notes_from_transcript("x" * 100000)

@pytest.mark.asyncio
async def test_extract_notes_retry_on_rate_limit():
    """Test retry on rate limit"""
    service = NoteExtractionService(api_key="test-key-123", retries=3)
    
    mock_response = {"key_topics": [], ...}  # Success response
    
    with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        # Fail twice, succeed on 3rd attempt
        mock_create.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Rate limit exceeded"),
            AsyncMock(return_value=type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,), {'content': json.dumps(mock_response)})()})]})())
        ]
        
        result = await service.extract_notes_from_transcript("Sample transcript")
        
        assert mock_create.call_count == 3
```

---

## Summary of Improvements

| Issue | Current | Improved | Effort |
|-------|---------|----------|--------|
| Blocking sync client | 30-60s blocks event loop | Async client, non-blocking | 1-2h |
| Global singleton | Untestable, hidden deps | FastAPI Depends injection | 2-3h |
| Error handling | ~5% coverage | Structured errors, retries | 1-2h |
| Config scattered | 3 load_dotenv calls | Single config.py | 1h |
| Testing | 0% coverage | 20+ unit tests | 3-4h |
| **TOTAL** | | | **8-12h** |

