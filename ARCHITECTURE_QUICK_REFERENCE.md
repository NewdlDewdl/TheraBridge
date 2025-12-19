# TherapyBridge - Architecture Quick Reference

## File Locations for Key Components

### Backend Integration Points

#### Audio Pipeline Integration
- **Service Wrapper:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/services/transcription.py`
  - Function: `transcribe_audio_file(audio_path: str) -> Dict`
  - Imports: `from src.pipeline import AudioTranscriptionPipeline`
  - Blocking call: `pipeline.process(audio_path)`

#### Session Processing (Upload to Extraction)
- **Router:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/sessions.py`
  - Endpoint: `POST /api/sessions/upload` (line 235)
  - Background task: `process_audio_pipeline()` (line 109)
  - Database updates: Lines 136-232 (stage transitions)
  - Timeline generation: Lines 195-212 (auto-event creation)

#### Note Extraction Service
- **AI Service:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/services/note_extraction.py`
  - Extraction prompt: Lines 20-80
  - JSON schema: Lines 55-81
  - OpenAI call: `AsyncOpenAI(api_key=key).beta.chat.completions.parse()`

#### Analytics & Scheduling
- **Scheduler Config:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/scheduler.py`
  - APScheduler setup: Lines 27-50
  - Jobs registration: Line 78 in `main.py`

- **Aggregation Jobs:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/tasks/aggregation.py`
  - Daily stats: `aggregate_daily_stats()` (line 36)
  - Patient progress: `snapshot_patient_progress()`

#### Database Connection
- **Connection Pool:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/database.py`
  - Async engine: Lines 44-53 (asyncpg)
  - Sync engine: Lines 65-74 (psycopg2)
  - Pool config: Lines 26-29
  - Dependency: `get_db()` (line 87)

#### Database Models
- **ORM Models:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/models/db_models.py`
  - User: Lines 13-62 (authentication, roles)
  - TherapySession: Lines 98-135 (core domain)
  - TimelineEvent: Lines 138-177 (Feature 5)
  - TherapistPatient: Lines 77-95 (many-to-many junction)

#### API Endpoints
- **Sessions:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/sessions.py`
  - POST /api/sessions/upload (line 235)
  - GET /api/sessions/{id} (line 465)
  - GET /api/sessions/patients/{id}/timeline (line 592)
  - POST /api/sessions/patients/{id}/timeline (line 781)

- **Patients:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/patients.py`
  - POST /api/patients/ (create)
  - GET /api/patients/ (list)
  - GET /api/patients/{id} (detail)

- **Analytics:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/analytics.py`
  - GET /api/v1/analytics/dashboard

### Frontend Integration Points

#### API Client
- **Main Client:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/lib/api-client.ts`
  - Class: `ApiClient` (line 61)
  - Methods: `request<T>()`, `get<T>()`, `post<T>()`, `put<T>()`, `delete<T>()`
  - Token refresh: `handleTokenRefresh()` (line 140)

#### Hooks for Data Fetching
- **Session Processing:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/hooks/use-session-processing.ts`
  - Polling logic: 2-second intervals
  - Status checks: uploading → processed

- **Session Data:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/hooks/use-session-data.ts`
  - Fetches session details
  - Extracted notes retrieval

#### Pages & Components
- **Therapist Dashboard:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/app/therapist/page.tsx`
  - Patient list with stats
  - Session filtering/sorting

- **Patient Dashboard:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/app/patient/page.tsx`
  - Session summaries
  - Timeline view

### Audio Pipeline

#### Main Pipeline
- **CPU/API Version:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline.py`
  - Class: `AudioTranscriptionPipeline` (line 200+)
  - Method: `process(audio_path)` - main entry point
  - Returns: dict with segments, full_text, language, duration

- **Preprocessing:** `AudioPreprocessor` class
  - Method: `preprocess(audio_path, output_path)`
  - Trimming, normalization, format conversion

- **Transcription:** `WhisperTranscriber` class
  - Uses: OpenAI Whisper API (large-v3)
  - Chunking: For files >25MB

- **Diarization:** `SpeakerDiarizer` class
  - Uses: pyannote-audio 3.1
  - Speaker detection: 2 speakers (Therapist, Client)

#### GPU Version (Optional)
- **GPU Pipeline:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline_gpu.py`
  - Uses: faster-whisper locally
  - GPU provider: Vast.ai (not yet integrated)

### Database Migrations

- **Location:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/alembic/versions/`
- **Key Migrations:**
  - `808b6192c57c_add_authentication_schema_and_missing_.py` - Auth tables
  - `d4e5f6g7h8i9_add_timeline_events_table.py` - Timeline (Feature 5)
  - `e5f6g7h8i9j0_add_goal_tracking_tables.py` - Goal tracking (Feature 6)
  - `e4f5g6h7i8j9_add_export_tables.py` - Export/reporting (Feature 7)
  - `g7h8i9j0k1l2_add_security_compliance_tables.py` - HIPAA (Feature 8)

### Configuration & Environment

- **Backend .env:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/.env`
  - DATABASE_URL (line 14)
  - OPENAI_API_KEY (line 47)
  - JWT_SECRET_KEY (line 62)
  - ENCRYPTION_MASTER_KEY (line 68)

- **Frontend .env.local:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/.env.local`
  - NEXT_PUBLIC_API_URL
  - NEXT_PUBLIC_USE_REAL_API

- **Audio Pipeline .env:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/.env`
  - OPENAI_API_KEY
  - HF_TOKEN (HuggingFace for pyannote)

### Testing

- **Backend Tests:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/tests/`
  - `conftest.py` - Pytest fixtures (auth users, database)
  - `test_auth_integration.py` - Authentication flow tests
  - `test_extraction_service.py` - AI extraction tests
  - `routers/test_sessions.py` - Session endpoint tests

- **Audio Pipeline Tests:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/tests/`
  - `test_full_pipeline.py` - Complete pipeline test

---

## Data Flow Sequences

### Upload → Processing → Display

```
1. Frontend: POST /api/sessions/upload
   └─> Backend: sessions.py:upload_audio_session() (line 235)
       ├─ Validate file (line 281)
       ├─ Create Session record (line 298-308)
       ├─ Save audio file (line 310-349)
       ├─ Queue background task (line 369)
       └─ Return Session (status: "uploading")

2. Background: process_audio_pipeline() (line 109)
   ├─ Stage 1: Update status → "transcribing"
   ├─ Stage 2: Call transcription.py:transcribe_audio_file() (line 146)
   │   └─> AudioTranscriptionPipeline.process()
   │       ├─ Preprocess
   │       ├─ Whisper transcribe
   │       └─ Pyannote diarize
   │   └─> Update DB with transcript_segments (line 150-160)
   │
   ├─ Stage 3: Update status → "extracting_notes"
   ├─ Stage 4: Call note_extraction.py:extract_notes() (line 164-184)
   │   └─> GPT-4o extraction
   │   └─> Update DB with extracted_notes (line 186-193)
   │
   ├─ Stage 5: Call timeline.py:auto_generate_session_event() (line 200)
   │   └─> Create TimelineEvent record
   │
   └─ Final: Update status → "processed"

3. Frontend: GET /api/sessions/{id} (polling every 2 sec)
   └─> Backend: sessions.py:get_session() (line 465)
       └─> Return current Session with all fields
           (frontend displays when status == "processed")
```

### Timeline Query

```
Frontend: GET /api/sessions/patients/{patient_id}/timeline
  └─> Backend: sessions.py:get_patient_timeline() (line 592)
      ├─ Get pagination cursor
      ├─ Query TimelineEvent (patient_id match)
      ├─ Apply filters (date, type, importance)
      ├─ Order by event_date DESC
      ├─ Paginate (cursor-based, limit 20)
      └─> Return TimelineEventResponse[]
```

### Analytics Aggregation

```
Scheduler: Daily at 0 UTC
  └─> tasks/aggregation.py:aggregate_daily_stats() (line 36)
      ├─ Calculate yesterday's date
      ├─ Query therapy_sessions grouped by therapist_id
      ├─ Calculate metrics:
      │  ├─ total_sessions: COUNT(*)
      │  ├─ total_patients_seen: COUNT(DISTINCT patient_id)
      │  └─ avg_session_duration: AVG(duration_seconds)
      ├─ Upsert into daily_stats (ON CONFLICT DO UPDATE)
      └─ Log results
```

---

## Key Performance Characteristics

### Processing Times
- Audio upload validation: ~100ms
- File save (1MB chunks): ~1-2 sec per 100MB
- Transcription (Whisper API): 5-7 min for 23 min audio
- AI extraction (GPT-4o): ~20 sec
- Timeline event creation: ~5 sec
- **Total:** ~7-10 minutes per session

### Database Operations
- Session creation: <10ms
- Transcript update: <100ms
- Extracted notes update: <50ms
- Timeline query (20 items): <50ms
- Timeline pagination: <100ms

### Concurrency Limits
- Thread pool workers: ~5-8 (CPU count + 4)
- DB connection pool: 20-30 total
- Max concurrent uploads: ~5 (limited by thread pool)
- Max timeline queries: ~30 (limited by DB pool)

### Storage Usage
- Audio file (1 hour @ 64kbps MP3): ~27MB
- Transcript (typed): ~5-10KB per hour
- Extracted notes (JSON): ~5-10KB per session
- Timeline events: ~1-2KB per session
- **Per session total:** ~27-28MB (mostly audio)

---

## Environment Variables (Complete List)

### Backend (backend/.env)
```
ENVIRONMENT=development
DEBUG=true  # CRITICAL: false in production
DATABASE_URL=postgresql+asyncpg://...
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o
JWT_SECRET_KEY=...
ENCRYPTION_MASTER_KEY=...
ENABLE_ANALYTICS_SCHEDULER=true
```

### Frontend (frontend/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_REAL_API=true  # false = use mock data
```

### Audio Pipeline (audio-transcription-pipeline/.env)
```
OPENAI_API_KEY=sk-proj-...
HF_TOKEN=hf_...  # HuggingFace for pyannote
```

---

## API Response Formats

### Session Response
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "therapist_id": "uuid",
  "session_date": "2025-12-19T10:00:00",
  "duration_seconds": 1380,
  "audio_filename": "session.mp3",
  "status": "processed",
  "transcript_text": "...",
  "transcript_segments": [
    {"speaker": "Therapist", "text": "...", "start": 0.0, "end": 5.2}
  ],
  "extracted_notes": {
    "key_topics": ["..."],
    "mood": "positive",
    "risk_flags": []
  },
  "created_at": "2025-12-19T10:00:00"
}
```

### Timeline Event Response
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "event_type": "session",
  "event_subtype": "completed",
  "event_date": "2025-12-19T10:00:00",
  "title": "Session - Positive Mood",
  "description": "...",
  "event_metadata": {
    "mood": "positive",
    "key_topics": ["..."],
    "risk_flags": []
  },
  "importance": "normal",
  "created_at": "2025-12-19T10:00:00"
}
```

### Timeline Summary Response
```json
{
  "total_events": 42,
  "events_by_type": {
    "session": 10,
    "milestone": 3,
    "goal": 5
  },
  "milestones_achieved": 3,
  "recent_highlights": ["..."]
}
```

---

## Critical Paths & Dependencies

### Session Processing Critical Path
1. File I/O (sequential): ~2 sec
2. Transcription (blocking): ~5-7 min
3. Note extraction: ~20 sec
4. Timeline creation: ~5 sec
**Total blocking time:** ~7 minutes per upload

### Database Critical Path
1. Session creation: 1 query
2. Update to transcribed: 1 query
3. Update to processed: 1 query
4. Timeline insert: 1 query
**Total queries:** 4 sequential, <500ms cumulative

### API Critical Path
1. Validate + create: ~100ms
2. Background task queued
3. Request returns immediately
4. Frontend polls every 2 sec until complete
**Total latency to user:** Immediate feedback + polling

