# Granular Logging & Real-Time Updates Implementation Plan

**Date:** 2025-12-28
**Status:** Ready for Implementation

---

## Overview

Add maximum-granularity logging throughout the demo pipeline and implement Server-Sent Events (SSE) for real-time per-session updates with loading states on individual cards.

---

## Current State Analysis

**What works:**
- ✅ Pipeline executes (transcripts → Wave 1 → Wave 2)
- ✅ Frontend polls `/api/demo/status` every 5s for completion
- ✅ Auto-refresh on Wave 1 and Wave 2 completion (all cards together)
- ✅ Basic logging exists (emoji-prefixed print statements)

**What's missing:**
- ❌ Granular timestamped logging with event details
- ❌ Per-session completion tracking (only tracks aggregate counts)
- ❌ Real-time updates (currently 5s polling delay)
- ❌ Individual card loading states (all cards update together)
- ❌ Log file persistence and API access
- ❌ Detailed performance metrics (duration, token counts, errors)

**Key constraints:**
- Railway ephemeral filesystem (logs reset on redeploy)
- SSE works over HTTP (no WebSocket infrastructure needed)
- Must handle parallel execution (10 sessions simultaneously in Wave 1)
- Frontend uses Next.js 16 + React 19

---

## Desired End State

**User experience:**
1. User initializes demo → sees 10 session cards immediately
2. **Real-time updates per session** (no polling delay):
   - Session 3 finishes Wave 1 → Session 3 card shows loading → updates with mood/topics
   - Session 7 finishes Wave 1 → Session 7 card shows loading → updates
   - etc.
3. Same behavior for Wave 2 completion (individual session updates)
4. Developer can monitor logs via:
   - Railway dashboard (stdout)
   - API endpoint: `GET /api/demo/logs/{patient_id}`
   - Log files on Railway filesystem (ephemeral)

**Verification:**
- Visit Railway logs → see granular timestamped events
- Call `/api/demo/logs/{patient_id}` → get structured log JSON
- Open frontend → connect to SSE → see real-time events in console
- Individual session cards grey out and update as their analysis completes

---

## What We're NOT Doing

- ❌ WebSockets (using SSE instead - simpler, HTTP-based)
- ❌ Permanent log storage in Supabase (using ephemeral files for now)
- ❌ UI display of logs (building API access only, UI comes later)
- ❌ Retry logic beyond single automatic retry
- ❌ Real-time progress bars (just completion events)
- ❌ Cancellation/pause functionality

---

## Implementation Approach

**Strategy:** Bottom-up implementation
1. Add granular logging infrastructure to scripts
2. Implement SSE event emission from background tasks
3. Create SSE endpoint in FastAPI backend
4. Build frontend SSE client hook
5. Add per-session loading states to cards
6. Create log file storage and API endpoint

**Technology choices:**
- **SSE over WebSockets:** Simpler, HTTP-based, one-way (server → client) is sufficient
- **In-memory event queue:** Background tasks write events, SSE endpoint streams them
- **Structured logging:** JSON format for easy parsing, text format for human readability
- **Python `logging` module:** Standard library, integrates with FastAPI

---

## Phase 1: Granular Logging Infrastructure

### Overview
Add timestamped, structured logging to all pipeline scripts with maximum granularity.

### Changes Required:

#### 1.1 Create Centralized Logger Utility

**File:** `backend/app/utils/pipeline_logger.py` (NEW)

**Purpose:** Centralized logging with structured output, file writing, and event emission

```python
"""
Pipeline Logger - Granular logging for demo pipeline
Supports stdout, file output, and SSE event emission
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

# Log event types
class LogPhase(str, Enum):
    TRANSCRIPT = "TRANSCRIPT"
    WAVE1 = "WAVE1"
    WAVE2 = "WAVE2"

class LogEvent(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    FILE_LOAD = "FILE_LOAD"
    DB_UPDATE = "DB_UPDATE"
    MOOD_ANALYSIS = "MOOD_ANALYSIS"
    TOPIC_EXTRACTION = "TOPIC_EXTRACTION"
    BREAKTHROUGH_DETECTION = "BREAKTHROUGH_DETECTION"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"

# Global event queue for SSE (in-memory)
_event_queue: Dict[str, list] = {}

class PipelineLogger:
    """Enhanced logger with structured output and event emission"""

    def __init__(self, patient_id: str, phase: LogPhase):
        self.patient_id = patient_id
        self.phase = phase
        self.logger = logging.getLogger(f"pipeline.{phase.value}")

        # Ensure log directory exists
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create patient-specific log file
        self.log_file = self.log_dir / f"pipeline_{patient_id}.log"

        # Initialize event queue for this patient
        if patient_id not in _event_queue:
            _event_queue[patient_id] = []

    def log_event(
        self,
        event: LogEvent,
        session_id: Optional[str] = None,
        session_date: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a structured event with timestamp"""

        timestamp = datetime.utcnow()

        # Build structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat() + "Z",
            "patient_id": self.patient_id,
            "phase": self.phase.value,
            "event": event.value,
            "status": status,
        }

        if session_id:
            log_entry["session_id"] = session_id
        if session_date:
            log_entry["session_date"] = session_date
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)
        if details:
            log_entry["details"] = details

        # Format for human readability (stdout)
        session_info = f"[{session_date}]" if session_date else ""
        duration_info = f"({duration_ms:.0f}ms)" if duration_ms else ""
        details_info = f" {json.dumps(details)}" if details else ""

        log_message = (
            f"[{self.phase.value}] {session_info} "
            f"{event.value} {status.upper()} {duration_info}{details_info}"
        )

        # Log to stdout (for Railway dashboard)
        if status == "failed":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)

        # Write to file (structured JSON)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Add to event queue for SSE
        _event_queue[self.patient_id].append(log_entry)

    @staticmethod
    def get_events(patient_id: str) -> list:
        """Get all events for a patient (for SSE streaming)"""
        return _event_queue.get(patient_id, [])

    @staticmethod
    def clear_events(patient_id: str):
        """Clear event queue after SSE client disconnects"""
        if patient_id in _event_queue:
            _event_queue[patient_id] = []
```

---

#### 1.2 Update Transcript Population Script

**File:** `backend/scripts/seed_all_sessions.py`

**Changes:** Add granular logging with timestamps

**Line 26 - Add import:**
```python
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent
```

**Line 145-167 - Replace `process_single_session` function:**
```python
async def process_single_session(
    patient_id: str,
    filename: str,
    session_date: str,
    index: int,
    total: int
) -> Tuple[bool, str]:
    """Process a single session file (async) with granular logging"""

    logger = PipelineLogger(patient_id, LogPhase.TRANSCRIPT)
    session_id = f"session_{session_date}"  # Temporary ID for logging

    try:
        # START event
        logger.log_event(
            LogEvent.START,
            session_id=session_id,
            session_date=session_date,
            details={"index": index, "total": total, "filename": filename}
        )

        # FILE_LOAD start
        load_start = datetime.now()
        loop = asyncio.get_event_loop()
        transcript_data = await loop.run_in_executor(
            None, load_transcript_from_file, filename
        )
        load_duration = (datetime.now() - load_start).total_seconds() * 1000

        segment_count = len(transcript_data.get("segments", []))
        duration = transcript_data.get("metadata", {}).get("duration", 0) / 60

        # FILE_LOAD complete
        logger.log_event(
            LogEvent.FILE_LOAD,
            session_id=session_id,
            session_date=session_date,
            duration_ms=load_duration,
            details={
                "segments": segment_count,
                "duration_minutes": round(duration, 1),
                "file_size_kb": round(len(json.dumps(transcript_data)) / 1024, 2)
            }
        )

        print(f"[{index}/{total}] ✓ Loaded {filename}: {segment_count} segments, {duration:.0f} min")

        # DB_UPDATE start
        db_start = datetime.now()
        if await populate_session_transcript(patient_id, session_date, transcript_data):
            db_duration = (datetime.now() - db_start).total_seconds() * 1000

            # DB_UPDATE complete
            logger.log_event(
                LogEvent.DB_UPDATE,
                session_id=session_id,
                session_date=session_date,
                duration_ms=db_duration
            )

            print(f"[{index}/{total}] ✓ Updated session {session_date}")

            # COMPLETE event
            total_duration = load_duration + db_duration
            logger.log_event(
                LogEvent.COMPLETE,
                session_id=session_id,
                session_date=session_date,
                duration_ms=total_duration
            )

            return (True, f"Success: {filename}")
        else:
            logger.log_event(
                LogEvent.FAILED,
                session_id=session_id,
                session_date=session_date,
                status="failed",
                details={"error": "No session found in database"}
            )
            return (False, f"Failed: No session found for {session_date}")

    except FileNotFoundError as e:
        logger.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": f"File not found: {filename}"}
        )
        return (False, f"File not found: {filename}")
    except Exception as e:
        logger.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": str(e)}
        )
        return (False, f"Error processing {filename}: {e}")
```

---

#### 1.3 Update Wave 1 Analysis Script

**File:** `backend/scripts/seed_wave1_analysis.py`

**Changes:** Add granular logging for each analysis step

**Line 12 - Add imports:**
```python
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent
from datetime import datetime
```

**Lines 206-233 - Replace `process_session` function:**
```python
async def process_session(session: Dict[str, Any], index: int, total: int):
    """Process a single session with all Wave 1 analyses - granular logging"""
    session_id = session["id"]
    session_date = session.get("session_date", "unknown")
    patient_id = session.get("patient_id")

    logger_instance = PipelineLogger(patient_id, LogPhase.WAVE1)

    # START event
    logger_instance.log_event(
        LogEvent.START,
        session_id=session_id,
        session_date=session_date,
        details={"index": index + 1, "total": total}
    )

    logger.info(f"\n[{index + 1}/{total}] Processing session {session_date} ({session_id})")

    # Run all 3 analyses with individual logging
    updates = {}

    # MOOD_ANALYSIS
    mood_start = datetime.now()
    logger_instance.log_event(
        LogEvent.MOOD_ANALYSIS,
        session_id=session_id,
        session_date=session_date,
        status="started"
    )

    mood_result = await run_mood_analysis(session)

    if mood_result:
        mood_duration = (datetime.now() - mood_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.MOOD_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=mood_duration,
            details={
                "mood_score": mood_result.get("mood_score"),
                "confidence": mood_result.get("mood_confidence")
            }
        )
        updates.update(mood_result)
    else:
        logger_instance.log_event(
            LogEvent.MOOD_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="failed"
        )

    # TOPIC_EXTRACTION
    topic_start = datetime.now()
    logger_instance.log_event(
        LogEvent.TOPIC_EXTRACTION,
        session_id=session_id,
        session_date=session_date,
        status="started"
    )

    topic_result = await run_topic_extraction(session)

    if topic_result:
        topic_duration = (datetime.now() - topic_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.TOPIC_EXTRACTION,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=topic_duration,
            details={
                "topics_count": len(topic_result.get("topics", [])),
                "technique": topic_result.get("technique")
            }
        )
        updates.update(topic_result)
    else:
        logger_instance.log_event(
            LogEvent.TOPIC_EXTRACTION,
            session_id=session_id,
            session_date=session_date,
            status="failed"
        )

    # BREAKTHROUGH_DETECTION
    breakthrough_start = datetime.now()
    logger_instance.log_event(
        LogEvent.BREAKTHROUGH_DETECTION,
        session_id=session_id,
        session_date=session_date,
        status="started"
    )

    breakthrough_result = await run_breakthrough_detection(session)

    if breakthrough_result:
        breakthrough_duration = (datetime.now() - breakthrough_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.BREAKTHROUGH_DETECTION,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=breakthrough_duration,
            details={
                "has_breakthrough": breakthrough_result.get("has_breakthrough"),
                "candidates": len(breakthrough_result.get("breakthrough_candidates", []))
            }
        )
        updates.update(breakthrough_result)
    else:
        logger_instance.log_event(
            LogEvent.BREAKTHROUGH_DETECTION,
            session_id=session_id,
            session_date=session_date,
            status="failed"
        )

    # Update database
    if updates:
        db_start = datetime.now()
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="started"
        )

        await update_session_wave1(session_id, updates)

        db_duration = (datetime.now() - db_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=db_duration,
            details={"fields_updated": len(updates)}
        )

        # COMPLETE event
        total_duration = mood_duration + topic_duration + breakthrough_duration + db_duration
        logger_instance.log_event(
            LogEvent.COMPLETE,
            session_id=session_id,
            session_date=session_date,
            duration_ms=total_duration
        )

        logger.info(f"[{index + 1}/{total}] ✅ Session complete")
    else:
        logger_instance.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": "No results to update"}
        )
        logger.warning(f"[{index + 1}/{total}] ⚠️  No results to update")
```

---

#### 1.4 Update Wave 2 Analysis Script

**File:** `backend/scripts/seed_wave2_analysis.py`

**Changes:** Similar granular logging for Wave 2

**Line 12 - Add imports:**
```python
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent
from datetime import datetime
```

**Lines 195-223 - Replace `process_session_wave2` function:**
```python
async def process_session_wave2(
    session: Dict[str, Any],
    index: int,
    total: int,
    previous_sessions: List[Dict[str, Any]],
    previous_cumulative_context: Optional[Dict[str, Any]]
):
    """Process a single session with Wave 2 analysis - granular logging"""
    session_id = session["id"]
    session_date = session.get("session_date", "unknown")
    patient_id = session.get("patient_id")

    logger_instance = PipelineLogger(patient_id, LogPhase.WAVE2)

    # START event with context depth
    context_depth = len(previous_sessions)
    logger_instance.log_event(
        LogEvent.START,
        session_id=session_id,
        session_date=session_date,
        details={
            "index": index + 1,
            "total": total,
            "context_depth": context_depth
        }
    )

    logger.info(f"\n[{index + 1}/{total}] Processing session {session_date} ({session_id})")

    # Build cumulative context
    cumulative_context = build_cumulative_context(previous_sessions, previous_cumulative_context)

    if cumulative_context:
        logger.info(f"  📚 Context depth: {context_depth} previous session(s)")
    else:
        logger.info(f"  📚 No previous context (first session)")

    # DEEP_ANALYSIS
    analysis_start = datetime.now()
    logger_instance.log_event(
        LogEvent.DEEP_ANALYSIS,
        session_id=session_id,
        session_date=session_date,
        status="started",
        details={"context_depth": context_depth}
    )

    deep_analysis = await run_deep_analysis(session, cumulative_context)

    if deep_analysis:
        analysis_duration = (datetime.now() - analysis_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DEEP_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=analysis_duration,
            details={
                "confidence": deep_analysis.get("confidence_score"),
                "has_insights": bool(deep_analysis.get("insights"))
            }
        )

        # DB_UPDATE
        db_start = datetime.now()
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="started"
        )

        await update_session_wave2(session_id, deep_analysis)

        db_duration = (datetime.now() - db_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=db_duration
        )

        # COMPLETE event
        total_duration = analysis_duration + db_duration
        logger_instance.log_event(
            LogEvent.COMPLETE,
            session_id=session_id,
            session_date=session_date,
            duration_ms=total_duration
        )

        logger.info(f"[{index + 1}/{total}] ✅ Session complete")
        return deep_analysis, cumulative_context
    else:
        logger_instance.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed"
        )
        logger.warning(f"[{index + 1}/{total}] ⚠️  No results to update")
        return None, cumulative_context
```

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax valid: `python3 -m py_compile backend/app/utils/pipeline_logger.py`
- [ ] Scripts import successfully: `python3 -c "from backend.app.utils.pipeline_logger import PipelineLogger"`
- [ ] Log directory created: `ls -la backend/logs/` shows directory exists

#### Manual Verification:
- [ ] Run pipeline locally, check Railway logs for timestamped events
- [ ] Verify log file created: `backend/logs/pipeline_{patient_id}.log` exists
- [ ] Open log file, confirm JSON structure with timestamps, phases, events
- [ ] Check interleaved logs during Wave 1 parallel execution

**Implementation Note:** After this phase, all pipeline operations will emit structured logs to stdout and file, ready for SSE consumption.

---

## Phase 2: Server-Sent Events (SSE) Implementation

### Overview
Add SSE endpoint to FastAPI backend for real-time event streaming to frontend.

### Changes Required:

#### 2.1 Create SSE Router

**File:** `backend/app/routers/sse.py` (NEW)

**Purpose:** SSE endpoint for streaming pipeline events

```python
"""
Server-Sent Events Router
Real-time pipeline event streaming
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils.pipeline_logger import PipelineLogger
import asyncio
import json

router = APIRouter(prefix="/api/sse", tags=["sse"])

async def event_generator(patient_id: str, request: Request):
    """
    SSE event generator - streams pipeline events to client

    Yields events in SSE format:
    data: {"event": "wave1_complete", "session_id": "...", ...}

    """
    last_event_index = 0

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Get all events for this patient
            events = PipelineLogger.get_events(patient_id)

            # Send new events since last check
            if len(events) > last_event_index:
                new_events = events[last_event_index:]

                for event in new_events:
                    # Format as SSE event
                    yield f"data: {json.dumps(event)}\n\n"

                last_event_index = len(events)

            # Sleep briefly to avoid tight loop
            await asyncio.sleep(0.5)  # 500ms interval

    finally:
        # Client disconnected, optionally clear old events
        # PipelineLogger.clear_events(patient_id)  # Uncomment to clear on disconnect
        pass


@router.get("/events/{patient_id}")
async def stream_events(patient_id: str, request: Request):
    """
    SSE endpoint - connect to receive real-time pipeline events

    Usage:
        const eventSource = new EventSource('/api/sse/events/{patient_id}');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Pipeline event:', data);
        };

    Returns:
        StreamingResponse with text/event-stream content type
    """
    return StreamingResponse(
        event_generator(patient_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

---

#### 2.2 Register SSE Router in Main App

**File:** `backend/app/main.py`

**Changes:** Add SSE router to app

**Find line with:** `from app.routers import demo, sessions, debug`

**Replace with:**
```python
from app.routers import demo, sessions, debug, sse
```

**Find line with:** `app.include_router(debug.router)`

**Add after it:**
```python
app.include_router(sse.router)
```

---

#### 2.3 Update CORS Configuration for SSE

**File:** `backend/app/main.py`

**Find:** `allow_methods=["*"]`

**Ensure EventSource is allowed (already should be with `["*"]`):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Includes GET for SSE
    allow_headers=["*"],
)
```

### Success Criteria:

#### Automated Verification:
- [ ] Backend starts without errors: `cd backend && uvicorn app.main:app --reload`
- [ ] SSE endpoint exists: `curl http://localhost:8000/api/sse/events/test-uuid` (should hang, waiting for events)
- [ ] Swagger docs show SSE endpoint: Visit `http://localhost:8000/docs`

#### Manual Verification:
- [ ] Initialize demo, get patient_id
- [ ] Connect to SSE: `curl http://localhost:8000/api/sse/events/{patient_id}` (should stream events as they occur)
- [ ] Verify events stream in real-time during pipeline execution
- [ ] Check event format is valid JSON

**Implementation Note:** SSE connection stays open until client disconnects or pipeline completes. Test with multiple concurrent connections.

---

## Phase 3: Enhanced Status Endpoint

### Overview
Update `/api/demo/status` to return per-session completion status.

### Changes Required:

#### 3.1 Update DemoStatusResponse Schema

**File:** `backend/app/routers/demo.py`

**Find line ~50:** `class DemoStatusResponse(BaseModel):`

**Replace entire class with:**
```python
class SessionStatus(BaseModel):
    """Individual session completion status"""
    session_id: str
    session_date: str
    has_transcript: bool
    wave1_complete: bool
    wave2_complete: bool


class DemoStatusResponse(BaseModel):
    """Enhanced demo status with per-session completion tracking"""
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool
    analysis_status: str  # "pending" | "processing" | "wave1_complete" | "wave2_complete"
    wave1_complete: int  # Total sessions with Wave 1 complete
    wave2_complete: int  # Total sessions with Wave 2 complete
    sessions: List[SessionStatus]  # Per-session status
```

---

#### 3.2 Update Status Endpoint Implementation

**File:** `backend/app/routers/demo.py`

**Find line ~320:** `@router.get("/status", response_model=DemoStatusResponse)`

**Replace entire function (lines 320-371) with:**
```python
@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Get current demo user status with per-session analysis progress

    Returns:
        DemoStatusResponse with user info, session count, and per-session completion
    """
    patient_id = demo_user["id"]

    # Fetch all sessions with analysis data
    sessions_response = db.table("therapy_sessions").select(
        "id, session_date, transcript, mood_score, deep_analysis"
    ).eq("patient_id", patient_id).order("session_date").execute()

    sessions = sessions_response.data or []
    session_count = len(sessions)

    # Build per-session status
    session_statuses = []
    wave1_complete_count = 0
    wave2_complete_count = 0

    for session in sessions:
        has_transcript = bool(session.get("transcript"))
        wave1_complete = session.get("mood_score") is not None
        wave2_complete = session.get("deep_analysis") is not None

        if wave1_complete:
            wave1_complete_count += 1
        if wave2_complete:
            wave2_complete_count += 1

        session_statuses.append(SessionStatus(
            session_id=session["id"],
            session_date=session["session_date"],
            has_transcript=has_transcript,
            wave1_complete=wave1_complete,
            wave2_complete=wave2_complete
        ))

    # Determine overall analysis status
    if wave2_complete_count == session_count:
        analysis_status = "wave2_complete"
    elif wave1_complete_count == session_count:
        analysis_status = "wave1_complete"
    elif wave1_complete_count > 0 or wave2_complete_count > 0:
        analysis_status = "processing"
    else:
        analysis_status = "pending"

    # Check if expired
    from datetime import datetime
    expires_at = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
    is_expired = expires_at < datetime.now(expires_at.tzinfo)

    return DemoStatusResponse(
        demo_token=demo_user["demo_token"],
        patient_id=patient_id,
        session_count=session_count,
        created_at=demo_user.get("created_at", ""),
        expires_at=demo_user["demo_expires_at"],
        is_expired=is_expired,
        analysis_status=analysis_status,
        wave1_complete=wave1_complete_count,
        wave2_complete=wave2_complete_count,
        sessions=session_statuses
    )
```

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax valid: `python3 -m py_compile backend/app/routers/demo.py`
- [ ] Backend starts: `uvicorn app.main:app --reload`
- [ ] Status endpoint returns new format: `curl http://localhost:8000/api/demo/status -H "X-Demo-Token: {token}"` shows `sessions` array

#### Manual Verification:
- [ ] Initialize demo, call `/api/demo/status`
- [ ] Verify `sessions` array contains all 10 sessions
- [ ] Verify `wave1_complete` and `wave2_complete` booleans update as pipeline runs
- [ ] Confirm individual session status matches database state

---

## Phase 4: Frontend SSE Client Hook

### Overview
Create React hook to connect to SSE endpoint and receive real-time events.

### Changes Required:

#### 4.1 Create SSE Client Hook

**File:** `frontend/hooks/use-pipeline-events.ts` (NEW)

**Purpose:** React hook for SSE connection and event handling

```typescript
"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface PipelineEvent {
  timestamp: string;
  patient_id: string;
  phase: "TRANSCRIPT" | "WAVE1" | "WAVE2";
  event: string;
  status: string;
  session_id?: string;
  session_date?: string;
  duration_ms?: number;
  details?: Record<string, any>;
}

interface UsePipelineEventsOptions {
  patientId: string;
  enabled?: boolean;
  onEvent?: (event: PipelineEvent) => void;
  onWave1SessionComplete?: (sessionId: string, sessionDate: string) => void;
  onWave2SessionComplete?: (sessionId: string, sessionDate: string) => void;
}

export function usePipelineEvents(options: UsePipelineEventsOptions) {
  const {
    patientId,
    enabled = true,
    onEvent,
    onWave1SessionComplete,
    onWave2SessionComplete,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleEvent = useCallback(
    (event: PipelineEvent) => {
      // Add to events list
      setEvents((prev) => [...prev, event]);

      // Call custom event handler
      if (onEvent) {
        onEvent(event);
      }

      // Detect Wave 1 session completion
      if (
        event.phase === "WAVE1" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 1 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave1SessionComplete) {
          onWave1SessionComplete(event.session_id, event.session_date);
        }
      }

      // Detect Wave 2 session completion
      if (
        event.phase === "WAVE2" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 2 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave2SessionComplete) {
          onWave2SessionComplete(event.session_id, event.session_date);
        }
      }
    },
    [onEvent, onWave1SessionComplete, onWave2SessionComplete]
  );

  useEffect(() => {
    if (!enabled || !patientId) {
      return;
    }

    // Create EventSource connection
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const eventSource = new EventSource(`${apiUrl}/api/sse/events/${patientId}`);

    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log("📡 SSE connected - listening for pipeline events");
      setIsConnected(true);
    };

    eventSource.onmessage = (messageEvent) => {
      try {
        const event: PipelineEvent = JSON.parse(messageEvent.data);
        handleEvent(event);
      } catch (error) {
        console.error("Failed to parse SSE event:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      setIsConnected(false);
      eventSource.close();
    };

    // Cleanup on unmount
    return () => {
      console.log("📡 SSE disconnected");
      eventSource.close();
      setIsConnected(false);
    };
  }, [enabled, patientId, handleEvent]);

  return {
    isConnected,
    events,
    latestEvent: events[events.length - 1] || null,
  };
}
```

---

#### 4.2 Update WaveCompletionBridge to Use SSE

**File:** `frontend/app/patient/components/WaveCompletionBridge.tsx`

**Replace entire file with:**
```typescript
"use client";

/**
 * WaveCompletionBridge - SSE-based Real-Time Updates
 *
 * Connects to SSE endpoint and triggers per-session updates as they complete.
 *
 * Behavior:
 *   - Connects to SSE stream on mount
 *   - When Wave 1 completes for a session: triggers loading state + refresh for that session
 *   - When Wave 2 completes for a session: triggers loading state + refresh for that session
 *   - Disconnects when all analysis complete
 */

import { useEffect, useState } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { demoApiClient } from "@/lib/demo-api-client";

export function WaveCompletionBridge() {
  const { refresh } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);

  // Get patient ID from demo token
  useEffect(() => {
    async function fetchPatientId() {
      const status = await demoApiClient.getStatus();
      if (status) {
        setPatientId(status.patient_id);
      }
    }
    fetchPatientId();
  }, []);

  // Connect to SSE and handle events
  const { isConnected, events } = usePipelineEvents({
    patientId: patientId || "",
    enabled: !!patientId,

    onWave1SessionComplete: (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 1 complete for ${sessionDate}! Refreshing session card...`
      );

      // TODO Phase 5: Show loading state on specific session card

      // Refresh data to show mood/topics
      refresh();
    },

    onWave2SessionComplete: (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 2 complete for ${sessionDate}! Refreshing session card...`
      );

      // TODO Phase 5: Show loading state on specific session card

      // Refresh data to show deep analysis
      refresh();
    },
  });

  // Log connection status
  useEffect(() => {
    if (isConnected) {
      console.log("✅ Real-time pipeline events connected");
    }
  }, [isConnected]);

  // Log events for debugging
  useEffect(() => {
    if (events.length > 0) {
      const latest = events[events.length - 1];
      console.log(
        `[${latest.phase}] ${latest.session_date || "N/A"} - ${latest.event}`,
        latest.details || ""
      );
    }
  }, [events]);

  return null;
}
```

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit --skipLibCheck`
- [ ] No ESLint errors: `cd frontend && npm run lint`

#### Manual Verification:
- [ ] Initialize demo, open browser console
- [ ] See `📡 SSE connected` message
- [ ] See real-time event logs as pipeline runs
- [ ] See `✅ Wave 1 complete for 2025-01-10!` messages
- [ ] Verify `refresh()` is called when events fire
- [ ] Check Network tab: SSE connection stays open (type: `eventsource`)

---

## Phase 5: Per-Session Loading States

### Overview
Add loading overlays to individual session cards when their analysis completes.

### Changes Required:

#### 5.1 Add Loading State to SessionDataContext

**File:** `frontend/app/patient/contexts/SessionDataContext.tsx`

**Find line 19:** `interface SessionDataContextType {`

**Add new field after line 29:**
```typescript
  /** Session IDs currently loading (showing overlay) */
  loadingSessions: Set<string>;
  /** Set a session as loading */
  setSessionLoading: (sessionId: string, loading: boolean) => void;
```

**Find line 46:** `export function SessionDataProvider({ children }: { children: ReactNode }) {`

**Add state management:**
```typescript
export function SessionDataProvider({ children }: { children: ReactNode }) {
  const data = usePatientSessions();
  const [loadingSessions, setLoadingSessions] = useState<Set<string>>(new Set());

  const setSessionLoading = useCallback((sessionId: string, loading: boolean) => {
    setLoadingSessions((prev) => {
      const next = new Set(prev);
      if (loading) {
        next.add(sessionId);
      } else {
        next.delete(sessionId);
      }
      return next;
    });
  }, []);

  return (
    <SessionDataContext.Provider value={{ ...data, loadingSessions, setSessionLoading }}>
      {children}
    </SessionDataContext.Provider>
  );
}
```

---

#### 5.2 Update WaveCompletionBridge with Loading States

**File:** `frontend/app/patient/components/WaveCompletionBridge.tsx`

**Replace `onWave1SessionComplete` callback:**
```typescript
onWave1SessionComplete: async (sessionId, sessionDate) => {
  console.log(
    `🔄 Wave 1 complete for ${sessionDate}! Showing loading state...`
  );

  // Show loading overlay on this session card
  setSessionLoading(sessionId, true);

  // Small delay to ensure loading state is visible
  await new Promise(resolve => setTimeout(resolve, 100));

  // Refresh data to get mood/topics
  await refresh();

  // Hide loading overlay
  setSessionLoading(sessionId, false);
},

onWave2SessionComplete: async (sessionId, sessionDate) => {
  console.log(
    `🔄 Wave 2 complete for ${sessionDate}! Showing loading state...`
  );

  // Show loading overlay on this session card
  setSessionLoading(sessionId, true);

  // Small delay to ensure loading state is visible
  await new Promise(resolve => setTimeout(resolve, 100));

  // Refresh data to get deep analysis
  await refresh();

  // Hide loading overlay
  setSessionLoading(sessionId, false);
},
```

**Add import at top:**
```typescript
import { useSessionData } from "../contexts/SessionDataContext";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  // ... rest of component
}
```

---

#### 5.3 Create LoadingOverlay Component

**File:** `frontend/app/patient/components/LoadingOverlay.tsx` (NEW)

**Purpose:** Reusable loading overlay matching theme

```typescript
"use client";

import { motion } from "framer-motion";

interface LoadingOverlayProps {
  visible: boolean;
}

export function LoadingOverlay({ visible }: LoadingOverlayProps) {
  if (!visible) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="absolute inset-0 z-50 flex items-center justify-center"
      style={{
        backgroundColor: "rgba(236, 234, 229, 0.85)", // Light mode cream with transparency
      }}
    >
      {/* Dark mode overlay */}
      <div className="absolute inset-0 dark:bg-[rgba(26,22,37,0.85)] dark:block hidden" />

      {/* Spinner */}
      <div className="relative z-10">
        <div className="w-8 h-8 border-3 border-gray-300 dark:border-gray-600 border-t-gray-700 dark:border-t-gray-300 rounded-full animate-spin" />
      </div>
    </motion.div>
  );
}
```

---

#### 5.4 Add LoadingOverlay to Session Cards

**File:** Find where session cards are rendered (likely in a SessionCard component or similar)

**Example integration (adjust based on actual component structure):**

```typescript
import { LoadingOverlay } from "./LoadingOverlay";
import { useSessionData } from "../contexts/SessionDataContext";

export function SessionCard({ session }: { session: Session }) {
  const { loadingSessions } = useSessionData();
  const isLoading = loadingSessions.has(session.id);

  return (
    <div className="relative">
      {/* Existing card content */}
      <div className="card-content">
        {/* ... session data ... */}
      </div>

      {/* Loading overlay */}
      <LoadingOverlay visible={isLoading} />
    </div>
  );
}
```

**Note:** The exact implementation depends on your current session card component structure. Apply the same pattern to session detail modals.

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit --skipLibCheck`
- [ ] No console errors on page load

#### Manual Verification:
- [ ] Initialize demo, watch session cards
- [ ] When Wave 1 completes for a session, that card greys out briefly
- [ ] Card updates with mood/topics after loading overlay fades
- [ ] Same behavior for Wave 2 completion
- [ ] Loading overlay matches theme (cream in light mode, dark in dark mode)
- [ ] Spinner animates smoothly

---

## Phase 6: Log File API Endpoint

### Overview
Add API endpoint to retrieve log files for debugging.

### Changes Required:

#### 6.1 Add Log Endpoint to Demo Router

**File:** `backend/app/routers/demo.py`

**Add at end of file (before last line):**
```python
@router.get("/logs/{patient_id}")
async def get_pipeline_logs(
    patient_id: str,
    demo_user: dict = Depends(require_demo_auth)
):
    """
    Get pipeline logs for a patient

    Returns:
        JSON array of log events

    Note: Logs are ephemeral and reset on deployment
    """
    from pathlib import Path
    import json

    # Verify patient_id matches demo user
    if demo_user["id"] != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these logs")

    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_file = log_dir / f"pipeline_{patient_id}.log"

    if not log_file.exists():
        return {"logs": [], "message": "No logs found for this patient"}

    # Read log file and parse JSON lines
    logs = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    return {
        "patient_id": patient_id,
        "log_count": len(logs),
        "logs": logs
    }
```

### Success Criteria:

#### Automated Verification:
- [ ] Backend starts: `uvicorn app.main:app --reload`
- [ ] Endpoint exists: `curl http://localhost:8000/api/demo/logs/{patient_id} -H "X-Demo-Token: {token}"`

#### Manual Verification:
- [ ] Initialize demo, wait for pipeline to run
- [ ] Call `/api/demo/logs/{patient_id}` → returns array of log events
- [ ] Verify logs match what's in `backend/logs/pipeline_{patient_id}.log`
- [ ] Verify logs include timestamps, phases, events, details

---

## Testing Strategy

### Local Testing:

1. **Start backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Initialize demo** via frontend

4. **Monitor multiple sources:**
   - Backend terminal (stdout logs)
   - Browser console (SSE events)
   - `backend/logs/pipeline_{patient_id}.log` (structured logs)
   - Network tab (SSE connection)

### Railway Deployment Testing:

1. **Push to GitHub** → Railway auto-deploys

2. **Check Railway logs:**
   - Filter for `[TRANSCRIPT]`, `[WAVE1]`, `[WAVE2]`
   - Verify timestamped events appear
   - Check for errors

3. **Test SSE connection:**
   ```bash
   curl -N https://therabridge-backend.up.railway.app/api/sse/events/{patient_id}
   ```
   Should stream events as they occur

4. **Test log endpoint:**
   ```bash
   curl https://therabridge-backend.up.railway.app/api/demo/logs/{patient_id} \
     -H "X-Demo-Token: {token}"
   ```

5. **Frontend testing:**
   - Visit `https://therabridge.up.railway.app`
   - Initialize demo
   - Open browser console
   - Verify SSE connection
   - Watch session cards update individually
   - Check loading overlays appear on each card

### Edge Case Testing:

- [ ] Initialize demo, immediately disconnect SSE → reconnect → verify events catch up
- [ ] Initialize demo, close browser, reopen → SSE reconnects
- [ ] Run multiple demos simultaneously → verify logs don't mix
- [ ] Simulate Wave 1 failure (mock error) → verify retry logic
- [ ] Check log file size after 10 demos → verify it's manageable

---

## Performance Considerations

**SSE Connection Overhead:**
- Each client maintains open HTTP connection
- Minimal bandwidth (~1KB per event, ~50 events per demo)
- Connection auto-closes when client leaves page

**Log File Growth:**
- Each demo generates ~500-1000 lines (~50KB)
- 100 demos = ~5MB of logs
- Railway ephemeral storage resets on deploy (not a concern)

**Event Queue Memory:**
- In-memory dict holds events per patient
- Each event ~500 bytes
- 10 patients × 100 events = ~500KB memory
- Can add cleanup: clear events after Wave 2 completes

**Optimizations (future):**
- Add `PipelineLogger.clear_events(patient_id)` after Wave 2 complete
- Compress old log files (gzip)
- Move to Supabase Storage for permanent logs

---

## Migration Notes

No database schema changes required.

**Deployment steps:**
1. Merge changes to main branch
2. Railway auto-deploys backend
3. Vercel/Railway auto-deploys frontend
4. Existing demos continue working (backwards compatible)
5. New demos use SSE + granular logging

**Backwards compatibility:**
- SSE is optional (frontend still works without it)
- Log files don't break existing functionality
- Status endpoint adds fields but keeps old ones

---

## References

- **SSE Specification:** https://html.spec.whatwg.org/multipage/server-sent-events.html
- **FastAPI StreamingResponse:** https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- **EventSource API:** https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- **React useEffect cleanup:** https://react.dev/reference/react/useEffect#disconnecting-from-the-server

---

## Implementation Checklist

### Phase 1: Granular Logging
- [ ] Create `backend/app/utils/pipeline_logger.py`
- [ ] Update `seed_all_sessions.py` with logging
- [ ] Update `seed_wave1_analysis.py` with logging
- [ ] Update `seed_wave2_analysis.py` with logging
- [ ] Test locally, verify log file creation

### Phase 2: SSE Implementation
- [ ] Create `backend/app/routers/sse.py`
- [ ] Register SSE router in `main.py`
- [ ] Update CORS config
- [ ] Test SSE connection locally

### Phase 3: Enhanced Status Endpoint
- [ ] Update `DemoStatusResponse` schema
- [ ] Update `get_demo_status()` implementation
- [ ] Test endpoint returns per-session status

### Phase 4: Frontend SSE Client
- [ ] Create `frontend/hooks/use-pipeline-events.ts`
- [ ] Update `WaveCompletionBridge.tsx`
- [ ] Test SSE connection in browser

### Phase 5: Loading States
- [ ] Update `SessionDataContext.tsx`
- [ ] Create `LoadingOverlay.tsx` component
- [ ] Add overlay to session cards
- [ ] Test loading states appear on individual cards

### Phase 6: Log API Endpoint
- [ ] Add `/api/demo/logs/{patient_id}` endpoint
- [ ] Test log retrieval

### Testing:
- [ ] Local end-to-end test
- [ ] Railway deployment test
- [ ] SSE connection test
- [ ] Log file verification
- [ ] Performance check

---

**Plan Status:** Ready for Implementation
**Estimated Implementation Time:** 3-4 hours
**Estimated Testing Time:** 30 minutes
**Total Time:** 4-5 hours
