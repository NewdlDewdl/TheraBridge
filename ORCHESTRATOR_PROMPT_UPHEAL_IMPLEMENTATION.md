# Orchestrator Task: Implement Upheal-Inspired Session Processing Pipeline

## 🎯 Objective

Implement fast, parallel audio processing pipeline and enhanced session management UI based on comprehensive Upheal competitive analysis. Transform TherapyBridge to match Upheal's speed and user experience.

## 📋 Context

**Analysis Document:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/UPHEAL_SESSIONS_PIPELINE_ANALYSIS.md`

Read this document FIRST - it contains:
- Complete breakdown of Upheal's sessions workflow
- Reverse-engineered audio processing pipeline
- Speed optimization strategies (how they process 1hr audio in ~30 seconds)
- Session UI patterns and components
- Code examples and implementation guidance

**Current State:**
- TherapyBridge has basic transcription pipeline (CPU + GPU versions)
- Audio processing is sequential (slow)
- Session UI lacks key features (granular controls, AI summaries on cards)
- No progress tracking during upload
- No anonymous session mode

**Goal:** Match or exceed Upheal's speed and feature set

---

## 📦 Deliverables

### 1. Backend: Parallel Audio Processing Pipeline
**Priority: CRITICAL**

**File:** `backend/app/services/audio_processing_service.py` (NEW)

Implement parallel processing service that runs transcription + diarization concurrently:

```python
class AudioProcessingService:
    async def process_session_audio(
        self,
        session_id: str,
        audio_file_path: str,
        client_id: Optional[str] = None
    ) -> dict:
        """
        Process audio with parallel execution
        Target: 30-60s for 1hr audio (matching Upheal)
        """
        # Step 1: Preprocess (normalize, denoise)
        # Step 2: Run transcription + diarization in PARALLEL with asyncio.gather()
        # Step 3: Merge transcript with speaker labels
        # Step 4: Generate AI notes with GPT-4
        # Step 5: Save to database
        # Step 6: Return structured result
```

**Integration Points:**
- Integrate with existing `backend/src/pipeline.py` (CPU version)
- Integrate with existing `backend/src/pipeline_gpu.py` (GPU version)
- Add WebSocket or Server-Sent Events for progress updates (0-100%)

**Performance Target:**
- 1-hour audio processed in < 60 seconds (currently slower)
- Progress updates every 5 seconds during processing

---

### 2. Backend: Enhanced Database Schema
**Priority: HIGH**

**File:** `backend/alembic/versions/XXXXX_add_upheal_features.py` (NEW migration)

Add these columns to `therapy_sessions` table:

```sql
-- Granular deletion tracking
ALTER TABLE therapy_sessions ADD COLUMN recording_deleted_at TIMESTAMP;
ALTER TABLE therapy_sessions ADD COLUMN transcript_deleted_at TIMESTAMP;

-- Anonymous mode
ALTER TABLE therapy_sessions ADD COLUMN is_anonymous BOOLEAN DEFAULT FALSE;

-- AI-generated summary for session cards
ALTER TABLE therapy_sessions ADD COLUMN ai_summary TEXT;

-- Processing status tracking
CREATE TYPE processing_status AS ENUM (
    'uploading',
    'preprocessing',
    'transcribing',
    'diarizing',
    'generating_notes',
    'completed',
    'failed'
);
ALTER TABLE therapy_sessions ADD COLUMN processing_status processing_status DEFAULT 'uploading';
ALTER TABLE therapy_sessions ADD COLUMN processing_progress INTEGER DEFAULT 0; -- 0-100%

-- Duration in minutes (calculated from audio)
ALTER TABLE therapy_sessions ADD COLUMN duration_mins INTEGER;
```

**Update Model:**
- Update `backend/app/models/db_models.py` TherapySession model with new fields
- Add helper methods: `delete_recording()`, `delete_transcript()`, `mark_anonymous()`

---

### 3. Backend: Session Management Endpoints
**Priority: HIGH**

**File:** `backend/app/routers/sessions.py` (UPDATE)

Add new endpoints:

```python
# Granular deletion
DELETE /api/sessions/{session_id}/recording
DELETE /api/sessions/{session_id}/transcript
DELETE /api/sessions/{session_id}  # Complete deletion

# Anonymous mode
PATCH /api/sessions/{session_id}/anonymous
  Body: { "is_anonymous": true }

# Regenerate notes with new template
POST /api/sessions/{session_id}/regenerate-notes
  Body: { "template_id": "uuid" }

# Processing status (for progress bar)
GET /api/sessions/{session_id}/status
  Response: { "status": "transcribing", "progress": 45 }
```

---

### 4. Frontend: Enhanced Session Cards
**Priority: HIGH**

**File:** `frontend/components/session/SessionCard.tsx` (NEW)

Implement session card matching Upheal's design:

```typescript
interface SessionCardProps {
  session: {
    id: string
    date: string
    duration_mins: number
    client_name: string
    is_anonymous: boolean
    ai_summary: string  // ⭐ Display on card
    processing_status?: string
    processing_progress?: number
  }
}

// Features:
// - Date & time display
// - Duration badge (e.g., "50 mins")
// - "Held by You" label
// - Client name or "Anonymous individual"
// - AI-generated summary (1-2 sentences)
// - Edit button
// - Context menu (⋮) with actions
// - Processing indicator if status != "completed"
```

---

### 5. Frontend: Session Context Menu
**Priority: HIGH**

**File:** `frontend/components/session/SessionContextMenu.tsx` (NEW)

Implement dropdown menu with granular actions:

```typescript
<DropdownMenu>
  <DropdownMenuItem>Reassign session</DropdownMenuItem>
  <DropdownMenuSeparator />
  <DropdownMenuItem className="text-destructive">
    Delete recording
  </DropdownMenuItem>
  <DropdownMenuItem className="text-destructive">
    Delete transcript
  </DropdownMenuItem>
  <DropdownMenuItem className="text-destructive">
    Delete session
  </DropdownMenuItem>
</DropdownMenu>
```

**Features:**
- Confirmation dialogs for destructive actions
- API calls to new deletion endpoints
- Optimistic UI updates
- Toast notifications

---

### 6. Frontend: Upload Progress UI
**Priority: MEDIUM**

**File:** `frontend/components/session/UploadProgress.tsx` (NEW)

Show real-time processing progress:

```typescript
interface UploadProgressProps {
  sessionId: string
  onComplete: () => void
}

// Features:
// - Progress bar (0-100%)
// - Status text ("Transcribing audio...", "Generating notes...")
// - Estimated time remaining
// - Cancel button
// - Real-time updates via WebSocket or polling
```

**Integration:**
- Poll `GET /api/sessions/{id}/status` every 2 seconds
- Or use WebSocket connection for real-time updates
- Display in modal during upload

---

### 7. Frontend: Anonymous Session Toggle
**Priority: LOW**

**File:** `frontend/components/session/AnonymousToggle.tsx` (NEW)

Add toggle in session detail/edit view:

```typescript
<Switch
  checked={session.is_anonymous}
  onCheckedChange={(checked) => toggleAnonymous(checked)}
  label="Mark as anonymous (hide client name)"
/>
```

---

### 8. Backend: Note Templates System
**Priority: MEDIUM**

**Files:**
- `backend/app/models/db_models.py` - Add `NoteTemplate` model
- `backend/app/routers/templates.py` - CRUD endpoints for templates
- `backend/alembic/versions/XXXXX_add_note_templates.py` - Migration

**Schema:**
```python
class NoteTemplate(Base):
    __tablename__ = "note_templates"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    name = Column(String(200))  # "SOAP Format", "DAP Format"
    template_content = Column(JSON)  # Structure for GPT-4 prompt
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime)
```

**Endpoints:**
```python
GET    /api/templates          # List user's templates
POST   /api/templates          # Create template
PATCH  /api/templates/{id}     # Update template
DELETE /api/templates/{id}     # Delete template
POST   /api/sessions/{id}/regenerate-notes  # Use template
```

---

## 🔧 Technical Requirements

### Performance Targets:
- ⚡ **Audio Processing:** < 60 seconds for 1-hour audio
- 🔄 **Progress Updates:** Every 2-5 seconds during processing
- 🚀 **UI Response:** < 100ms for all interactions
- 📊 **Parallel Execution:** Transcription + diarization must run concurrently

### Technology Stack:
- **Backend:** Python 3.13, FastAPI, asyncio, SQLAlchemy
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Audio:** Whisper API, pyannote 3.1 for diarization
- **AI:** OpenAI GPT-4o for note generation
- **Database:** PostgreSQL (Neon)

### Code Quality:
- ✅ Type hints in Python (all functions)
- ✅ TypeScript strict mode (no `any`)
- ✅ Error handling with try/catch
- ✅ Input validation (Pydantic on backend, Zod on frontend)
- ✅ Logging for debugging
- ✅ Unit tests for critical paths (parallel processing service)

---

## 📂 File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── audio_processing_service.py  ⭐ NEW - Main deliverable
│   │   ├── progress_tracker.py          ⭐ NEW - WebSocket/SSE for progress
│   │   └── note_template_service.py     ⭐ NEW - Template rendering
│   ├── routers/
│   │   ├── sessions.py                  🔄 UPDATE - Add new endpoints
│   │   └── templates.py                 ⭐ NEW - Template CRUD
│   ├── models/
│   │   └── db_models.py                 🔄 UPDATE - Add new columns/models
│   └── schemas/
│       └── session_schemas.py           🔄 UPDATE - Add new fields
├── alembic/versions/
│   ├── XXXXX_add_upheal_features.py     ⭐ NEW - Migration
│   └── XXXXX_add_note_templates.py      ⭐ NEW - Migration
└── tests/
    └── test_parallel_processing.py      ⭐ NEW - Critical tests

frontend/
├── components/
│   └── session/
│       ├── SessionCard.tsx              ⭐ NEW
│       ├── SessionContextMenu.tsx       ⭐ NEW
│       ├── UploadProgress.tsx           ⭐ NEW
│       ├── AnonymousToggle.tsx          ⭐ NEW
│       └── SessionDetail.tsx            🔄 UPDATE - Integrate new components
├── app/
│   └── therapist/
│       └── sessions/
│           └── page.tsx                 🔄 UPDATE - Use SessionCard
└── lib/
    ├── api-client.ts                    🔄 UPDATE - Add new endpoints
    └── websocket-client.ts              ⭐ NEW - For progress updates
```

---

## 🎯 Success Criteria

### Functional:
- ✅ Audio processing completes in < 60 seconds for 1-hour file
- ✅ Progress bar updates in real-time during processing
- ✅ Session cards display AI summaries
- ✅ Context menu allows granular deletion (recording/transcript/session)
- ✅ Anonymous mode hides client names
- ✅ Note templates can be created and applied

### Technical:
- ✅ Transcription + diarization run in parallel (asyncio.gather)
- ✅ Database migrations apply cleanly
- ✅ No breaking changes to existing functionality
- ✅ All new endpoints documented in API docs
- ✅ TypeScript compiles without errors
- ✅ Backend tests pass

### UX:
- ✅ Session cards match Upheal's information density
- ✅ Processing feels instant (progress visible within 2 seconds)
- ✅ Destructive actions require confirmation
- ✅ Toast notifications for all actions
- ✅ Responsive design (mobile + desktop)

---

## 🚨 Critical Constraints

1. **DO NOT break existing functionality**
   - Audio pipeline must remain backward compatible
   - Existing sessions must still work
   - Current UI components should continue to function

2. **Performance is critical**
   - Use `asyncio.gather()` for parallel execution (not sequential)
   - Avoid blocking operations in async functions
   - Use database indexes for new columns

3. **Security**
   - Validate all inputs (Pydantic schemas)
   - Check user permissions before deleting (can't delete other users' sessions)
   - Sanitize file uploads

4. **Data integrity**
   - Soft deletes for recordings/transcripts (use `deleted_at` timestamps)
   - Hard delete only when session is fully deleted
   - Maintain referential integrity

---

## 📚 Reference Materials

**MUST READ FIRST:**
- `UPHEAL_SESSIONS_PIPELINE_ANALYSIS.md` - Comprehensive analysis with code examples

**Existing Code to Integrate With:**
- `backend/src/pipeline.py` - Current CPU transcription pipeline
- `backend/src/pipeline_gpu.py` - Current GPU transcription pipeline
- `backend/app/models/db_models.py` - Database models
- `frontend/app/patient/dashboard-v2/` - Current dashboard UI
- `frontend/components/session/UploadModal.tsx` - Existing upload modal

**Testing:**
- `backend/tests/test_full_pipeline.py` - Existing pipeline tests (use as reference)
- `audio-transcription-pipeline/tests/samples/` - Test audio files

---

## 🏁 Execution Plan for Orchestrator

### Wave 1: Backend Core (Parallel)
**Agents: 3**
1. Agent 1: Create `audio_processing_service.py` with parallel execution
2. Agent 2: Create database migration for new columns
3. Agent 3: Update `db_models.py` with new fields and methods

### Wave 2: Backend APIs (Parallel)
**Agents: 2**
1. Agent 1: Add session management endpoints (DELETE recording/transcript, PATCH anonymous)
2. Agent 2: Create progress tracking system (WebSocket or polling endpoint)

### Wave 3: Frontend Components (Parallel)
**Agents: 3**
1. Agent 1: Create `SessionCard.tsx` with new design
2. Agent 2: Create `SessionContextMenu.tsx` with granular actions
3. Agent 3: Create `UploadProgress.tsx` with real-time updates

### Wave 4: Integration & Testing (Sequential)
**Agents: 2**
1. Agent 1: Integrate new components into session pages, update API client
2. Agent 2: Write tests for parallel processing, run full test suite

### Wave 5: Note Templates (Optional - if time permits)
**Agents: 2**
1. Agent 1: Create template model + migration
2. Agent 2: Create template endpoints + UI

---

## 💬 Questions to Clarify Before Starting

None - analysis document contains all necessary information. Proceed with implementation.

---

## 🎁 Bonus Features (If Time Permits)

1. **Export to PDF/DOCX** - Add export buttons to session detail
2. **Transcript Editing UI** - Allow inline editing of speaker labels
3. **Search Across Transcripts** - Full-text search for keywords
4. **Session Analytics** - Average duration, processing time, word count
5. **Batch Upload** - Upload multiple audio files at once

---

## 📝 Final Notes

- Use the comprehensive analysis document as your primary reference
- Code examples in the analysis are production-ready and can be adapted directly
- Focus on speed optimization - this is the key differentiator
- The goal is to match Upheal's UX while maintaining TherapyBridge's unique features
- Test with the sample audio files in `audio-transcription-pipeline/tests/samples/`

**Priority Order:** Backend parallel processing → Database schema → Session UI → Progress tracking → Note templates

Good luck! 🚀
