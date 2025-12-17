# Backend Services - Quick Reference Guide

## Service Summary Table

| Service | File | Lines | Type | Status | Async | Error Handling | Tests |
|---------|------|-------|------|--------|-------|----------------|-------|
| Transcription | `transcription.py` | 27 | Function | MVP | Yes (wrapper only) | None | None |
| NoteExtraction | `note_extraction.py` | 187 | Class | MVP | Partial (sync client) | Basic logging | None |
| **Total** | | **214** | Mixed | | | **~5%** | **0%** |

## Critical Issues Checklist

- [ ] Sync OpenAI client blocks async event loop (30-60s impact)
- [ ] No error handling in background tasks (silent failures)
- [ ] Global mutable singleton pattern (untestable)
- [ ] Environment config scattered across 3 files
- [ ] Path navigation is brittle (uses hardcoded relative paths)
- [ ] No service unit tests (0% coverage)
- [ ] No timeout/retry mechanisms
- [ ] Inconsistent service patterns (function vs class)

## Service Quick Reference

### NoteExtractionService
```
Location:  backend/app/services/note_extraction.py
Imported:  backend/app/routers/sessions.py (2 locations)
Consumes:  OpenAI API, TranscriptSegment schema
Returns:   ExtractedNotes schema
Cost:      $0.01-0.05 per session (GPT-4o)
Duration:  ~30-60 seconds
```

### TranscriptionService
```
Location:  backend/app/services/transcription.py
Imported:  backend/app/routers/sessions.py (1 location)
Consumes:  AudioTranscriptionPipeline (external), audio file path
Returns:   Dict with keys: full_text, segments, duration, language
Cost:      Varies (Whisper API or local GPU)
Duration:  ~30-120 seconds (depends on audio length)
```

## Dependency Map

```
sessions.py (ROUTER)
├── imports transcribe_audio_file()
│   └── instantiates AudioTranscriptionPipeline() on each call
└── imports get_extraction_service()
    └── returns singleton NoteExtractionService
        └── uses OpenAI AsyncClient... actually no, sync client!
```

## Configuration Sources

| Config | Current Location | Should Be |
|--------|-----------------|-----------|
| DATABASE_URL | `database.py` + `note_extraction.py` | `config.py` |
| OPENAI_API_KEY | `note_extraction.py` | `config.py` |
| PIPELINE_DIR | `transcription.py` hardcoded | `config.py` |
| LOG_LEVEL | Implicit | `config.py` |

## File-to-File Imports

```
main.py
├── database.init_db(), close_db()
├── routers.sessions
├── routers.patients
├── auth.router
└── middleware.rate_limit

routers/sessions.py
├── services.note_extraction (get_extraction_service)
├── services.transcription (transcribe_audio_file)
├── database (get_db)
└── models.db_models, schemas

services/note_extraction.py
├── openai.OpenAI (SYNC CLIENT - issue!)
├── models.schemas.ExtractedNotes
└── os, dotenv, json, time

services/transcription.py
├── AudioTranscriptionPipeline (external package)
├── sys.path manipulation
└── Path, typing
```

## Line-by-Line Critical Issues

| File | Line(s) | Issue | Severity | Fix |
|------|---------|-------|----------|-----|
| transcription.py | 9 | Hardcoded relative path | HIGH | Config param |
| transcription.py | 12 | Silent operation (no logging) | MEDIUM | Add logging |
| transcription.py | 26 | Sync pipeline in async context | MEDIUM | Use executor |
| note_extraction.py | 12 | Multiple load_dotenv calls | MEDIUM | Load once |
| note_extraction.py | 86-92 | API key handling duplication | LOW | Extract helper |
| note_extraction.py | 113-127 | Sync client blocks loop | CRITICAL | Use AsyncOpenAI |
| note_extraction.py | 178-187 | Global singleton | HIGH | Use FastAPI Depends |

## Usage Pattern Examples

### Current (Problematic):
```python
# routers/sessions.py line 76-80
extraction_service = get_extraction_service()
notes = await extraction_service.extract_notes_from_transcript(...)
# ^ Returns singleton, blocking async call
```

### Recommended:
```python
# routers/sessions.py (improved)
def get_extraction_service(config: Config) -> NoteExtractionService:
    return Depends(lambda: NoteExtractionService(api_key=config.openai_key))

@router.post("/extract-notes")
async def extract(
    transcript: str,
    extraction_service: NoteExtractionService = Depends(get_extraction_service)
):
    notes = await extraction_service.extract_notes_from_transcript(transcript)
```

## Performance Baseline

| Operation | Duration | Blocking? | Cost |
|-----------|----------|-----------|------|
| Upload + process session | ~90-180s | Yes (server) | $0.01-0.05 |
| Transcription | ~30-120s | Yes (Whisper) | Variable |
| Note extraction | ~30-60s | **Yes (blocks event loop!)** | $0.01-0.05 |
| DB save | <100ms | No | Free |

## Testing Strategy Needed

### Unit Test Template
```python
# tests/test_services/test_note_extraction.py
@pytest.mark.asyncio
async def test_extract_notes_success(mock_openai_response):
    service = NoteExtractionService(api_key="test-key")
    result = await service.extract_notes_from_transcript("sample transcript")
    assert isinstance(result, ExtractedNotes)
    assert len(result.key_topics) > 0

@pytest.mark.asyncio
async def test_extract_notes_timeout():
    service = NoteExtractionService(api_key="test-key", timeout=1)
    with pytest.raises(TimeoutError):
        await service.extract_notes_from_transcript("x" * 100000)

@pytest.mark.asyncio
async def test_extract_notes_retry_on_rate_limit():
    service = NoteExtractionService(api_key="test-key", retries=3)
    # Mock OpenAI to fail twice, succeed on 3rd
    result = await service.extract_notes_from_transcript(...)
    assert result is not None
```

## Improvement Task Breakdown

### Phase 1: Critical Fixes (4-6 hours)
- [ ] Upgrade to AsyncOpenAI
- [ ] Add try-catch in background tasks
- [ ] Add timeouts to API calls
- [ ] Create config.py with Settings

### Phase 2: Code Quality (8-10 hours)
- [ ] Extract BaseService class
- [ ] Add proper logging with structlog/loguru
- [ ] Implement DI pattern with FastAPI Depends
- [ ] Write 20+ service unit tests

### Phase 3: Optimization (6-8 hours)
- [ ] Add retry logic with exponential backoff
- [ ] Implement caching layer
- [ ] Add error telemetry/observability
- [ ] Document service layer architecture

## Checklist for Future PRs

When adding new services, ensure:
- [ ] Extends BaseService (not function-based)
- [ ] Initialized in main.py, injected via Depends()
- [ ] Has async/await for all I/O
- [ ] Includes timeout parameter
- [ ] Has structured logging
- [ ] Has unit tests with mocks
- [ ] Has error handling for 3+ scenarios
- [ ] Type hints for all parameters and returns
- [ ] Docstring with usage example

