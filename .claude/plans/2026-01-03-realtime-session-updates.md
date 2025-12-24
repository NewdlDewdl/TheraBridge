# Real-Time Granular Session Updates Implementation Plan

## Overview

Implement per-session real-time updates with loading overlays, fix SSE subprocess isolation bug, and optimize polling for granular updates. This will transform the current bulk refresh behavior (all 10 sessions re-render on any change) into smooth, per-card updates with visual feedback only on sessions that complete analysis.

## Current State Analysis

**Verified Production Behavior (Railway logs 2026-01-03 05:46):**
- ✅ Polling detects Wave 1/Wave 2 completion via count changes
- ✅ Full flow functional: transcripts load → Wave 1 analysis → Wave 2 prose generation
- ✅ SSE connects successfully but doesn't receive events
- ❌ Polling refreshes ALL sessions when ANY count changes
- ❌ SessionDetail page refreshes even when viewing different session
- ❌ No per-card loading indicators during analysis completion
- ❌ SSE broken due to subprocess isolation (events written to subprocess memory, never reach FastAPI)

**Timeline:**
1. **Demo Init (0-3s)**: Demo initialized, patient ID stored
2. **Transcripts Loading (0-30s)**: Sessions endpoint may timeout, polling starts at 1s
3. **Transcripts Complete (~30s)**: Polling detects `sessions: 0 → 10`, loads sessions
4. **Wave 1 Complete (~60s)**: Polling detects `wave1: 0 → 10`, **refreshes ALL 10 sessions**
5. **Wave 2 Complete (~9.6 min)**: Polling detects `wave2: 0 → 10`, **refreshes ALL 10 sessions again**
6. **Polling Stops**: When status reaches `wave2_complete`

## Desired End State

### User Experience:
- Individual session cards show loading overlay (500ms spinner + 200ms fade) ONLY when THAT session completes analysis
- Polling updates feel real-time (1s during Wave 1, 3s during Wave 2)
- SessionDetail page only updates if viewing session that changed
- Scroll position preserved during updates
- SSE provides instant updates (polling as fallback)

### Technical Specifications:
- `/api/demo/status` returns full analysis data per session (not just counts)
- Frontend tracks session state via `Map<sessionId, state>` for O(1) comparisons
- Adaptive polling: 1s during Wave 1 → 3s after Wave 1 complete → stop at Wave 2 complete
- Database-backed SSE event queue (cross-process accessible)
- Feature flags for safe rollout and rollback

### Verification:
```bash
# Manual test flow
1. Hard refresh → Demo init → 10 sessions load
2. Observe Session #1 complete Wave 1 → LoadingOverlay appears ONLY on card #1
3. Observe Session #2 complete Wave 1 → LoadingOverlay appears ONLY on card #2
4. Open SessionDetail for Session #3 → Session #5 completes Wave 1 → Detail page doesn't refresh
5. SSE connection in Railway logs shows events being sent and received
```

## What We're NOT Doing

- WebSocket implementation (using SSE only)
- Real-time updates for session detail transcript (only analysis updates)
- Optimistic UI updates (always fetch data from backend)
- Infinite polling (stops at `wave2_complete`)
- Backwards incompatible changes (feature flags allow rollback)

## Implementation Approach

**4-Phase Sequential Implementation:**
1. **Phase 1**: Backend - Enhance `/api/demo/status` for delta data
2. **Phase 2**: Frontend - Granular polling updates with per-session loading overlays
3. **Phase 3**: Backend - Database-backed SSE event queue
4. **Phase 4**: Frontend - SSE integration + feature flags + testing + documentation

**Why this order:**
- Phase 1 enables Phase 2 (frontend needs delta data from backend)
- Phase 2 provides immediate value (granular polling works standalone)
- Phase 3 fixes SSE infrastructure (database-backed events)
- Phase 4 integrates SSE + polishes UX (real-time updates)

---

## Phase 1: Backend - Enhance `/api/demo/status` for Delta Data

### Overview
Modify the `/api/demo/status` endpoint to return full analysis data per session (topics, mood_score, summary, prose_analysis) instead of just boolean flags. This enables frontend to detect exactly which sessions changed and what data to display without fetching from `/api/sessions/`.

### Changes Required

#### 1.1 Update SessionStatus Schema

**File**: `backend/app/routers/demo.py`
**Lines**: 427-513 (existing `/api/demo/status` endpoint)

**Current SessionStatus schema:**
```python
{
    "session_id": str,
    "session_date": str,
    "has_transcript": bool,
    "wave1_complete": bool,
    "wave2_complete": bool
}
```

**Enhanced SessionStatus schema:**
```python
from typing import Optional
from datetime import datetime

class SessionStatus(BaseModel):
    # Existing fields
    session_id: str
    session_date: str
    has_transcript: bool
    wave1_complete: bool
    wave2_complete: bool

    # NEW: Wave 1 analysis fields (nullable until Wave 1 completes)
    topics: Optional[list[str]] = None
    mood_score: Optional[float] = None
    summary: Optional[str] = None
    technique: Optional[str] = None
    action_items: Optional[list[str]] = None

    # NEW: Wave 2 analysis fields (nullable until Wave 2 completes)
    prose_analysis: Optional[str] = None
    deep_analysis: Optional[dict] = None

    # NEW: Timestamps for change detection
    last_wave1_update: Optional[str] = None  # ISO timestamp
    last_wave2_update: Optional[str] = None  # ISO timestamp

    # NEW: Change detection flag
    changed_since_last_poll: bool = False
```

#### 1.2 Modify Database Query

**File**: `backend/app/routers/demo.py`
**Function**: `get_demo_status` (lines 427-513)

**Current query (line ~470):**
```python
sessions_response = (
    db.table("therapy_sessions")
    .select("id, session_date, transcript, topics, mood_score, prose_analysis")
    .eq("patient_id", patient_id)
    .order("session_date")
    .execute()
)
```

**Enhanced query:**
```python
sessions_response = (
    db.table("therapy_sessions")
    .select("""
        id,
        session_date,
        transcript,
        topics,
        mood_score,
        summary,
        technique,
        action_items,
        prose_analysis,
        deep_analysis,
        topics_extracted_at,
        mood_analyzed_at,
        deep_analyzed_at,
        prose_generated_at
    """)
    .eq("patient_id", patient_id)
    .order("session_date")
    .execute()
)
```

#### 1.3 Transform Session Data

**File**: `backend/app/routers/demo.py`
**Location**: After database query (~line 480)

**Add transformation logic:**
```python
session_statuses = []
for session in sessions_response.data:
    # Determine Wave 1/Wave 2 completion
    wave1_complete = session.get("topics") is not None or session.get("mood_score") is not None
    wave2_complete = session.get("prose_analysis") is not None

    # Get timestamps (ISO format)
    last_wave1_update = None
    if session.get("topics_extracted_at"):
        last_wave1_update = session["topics_extracted_at"]
    elif session.get("mood_analyzed_at"):
        last_wave1_update = session["mood_analyzed_at"]

    last_wave2_update = None
    if session.get("prose_generated_at"):
        last_wave2_update = session["prose_generated_at"]
    elif session.get("deep_analyzed_at"):
        last_wave2_update = session["deep_analyzed_at"]

    # Build SessionStatus
    session_status = {
        "session_id": session["id"],
        "session_date": session.get("session_date", ""),
        "has_transcript": session.get("transcript") is not None,
        "wave1_complete": wave1_complete,
        "wave2_complete": wave2_complete,

        # Wave 1 fields (null if not complete)
        "topics": session.get("topics") if wave1_complete else None,
        "mood_score": session.get("mood_score") if wave1_complete else None,
        "summary": session.get("summary") if wave1_complete else None,
        "technique": session.get("technique") if wave1_complete else None,
        "action_items": session.get("action_items") if wave1_complete else None,

        # Wave 2 fields (null if not complete)
        "prose_analysis": session.get("prose_analysis") if wave2_complete else None,
        "deep_analysis": session.get("deep_analysis") if wave2_complete else None,

        # Timestamps
        "last_wave1_update": last_wave1_update,
        "last_wave2_update": last_wave2_update,

        # Change detection (frontend will override this based on comparison)
        "changed_since_last_poll": False  # Default, frontend determines this
    }

    session_statuses.append(session_status)
```

#### 1.4 Update Response Model

**File**: `backend/app/routers/demo.py`
**Location**: Response construction (~line 500)

**Current response:**
```python
return {
    "demo_token": demo_token,
    "patient_id": patient_id,
    "session_count": session_count,
    "created_at": demo_user["demo_created_at"],
    "expires_at": demo_user["demo_expires_at"],
    "is_expired": is_expired,
    "analysis_status": analysis_status,
    "wave1_complete": wave1_complete_count,
    "wave2_complete": wave2_complete_count,
    "sessions": session_statuses  # ← Now includes full analysis data
}
```

**No changes needed** - response structure remains the same, `sessions` array now contains richer data.

### Success Criteria

#### Automated Verification:
- [ ] Backend starts without errors: `cd backend && uvicorn app.main:app --reload`
- [ ] `/api/demo/status` returns 200 OK
- [ ] Response includes `sessions` array with all new fields
- [ ] `topics`, `mood_score`, `summary` are `null` when Wave 1 incomplete
- [ ] `prose_analysis`, `deep_analysis` are `null` when Wave 2 incomplete
- [ ] `last_wave1_update` and `last_wave2_update` are ISO timestamp strings
- [ ] Linting passes: `cd backend && ruff check .`

#### Manual Verification:
- [ ] Call `/api/demo/status` after demo init → all analysis fields are `null`
- [ ] Call `/api/demo/status` after Wave 1 completes → `topics` and `mood_score` populated
- [ ] Call `/api/demo/status` after Wave 2 completes → `prose_analysis` populated
- [ ] Timestamps match session database records

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Frontend - Granular Polling Updates

### Overview
Refactor frontend polling logic to detect per-session changes, show loading overlays only on changed cards, and implement adaptive polling intervals (1s during Wave 1, 3s during Wave 2).

### Changes Required

#### 2.1 Add Environment Variables

**File**: `frontend/.env.local.example`
**Changes**: Add new configuration variables

```bash
# Granular Updates Feature Flags
NEXT_PUBLIC_GRANULAR_UPDATES=true          # Enable per-session updates
NEXT_PUBLIC_SSE_ENABLED=false              # Enable SSE (disabled until Phase 4)

# Polling Configuration
NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000    # 1s during Wave 1
NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000    # 3s during Wave 2

# Loading Overlay Timing
NEXT_PUBLIC_LOADING_OVERLAY_DURATION=500   # 500ms spinner
NEXT_PUBLIC_LOADING_FADE_DURATION=200      # 200ms fade-out
NEXT_PUBLIC_STAGGER_DELAY=100              # 100ms delay between batch updates

# Debug Logging
NEXT_PUBLIC_DEBUG_POLLING=true             # Verbose console logs
```

**File**: `frontend/.env.local`
**Changes**: Copy from `.env.local.example` and set values

#### 2.2 Create Polling Configuration Module

**File**: `frontend/lib/polling-config.ts` (NEW FILE)
**Purpose**: Centralize polling configuration with type safety

```typescript
export const POLLING_CONFIG = {
  // Feature flags
  granularUpdatesEnabled: process.env.NEXT_PUBLIC_GRANULAR_UPDATES === 'true',
  sseEnabled: process.env.NEXT_PUBLIC_SSE_ENABLED === 'true',

  // Polling intervals (milliseconds)
  wave1Interval: parseInt(process.env.NEXT_PUBLIC_POLLING_INTERVAL_WAVE1 || '1000', 10),
  wave2Interval: parseInt(process.env.NEXT_PUBLIC_POLLING_INTERVAL_WAVE2 || '3000', 10),

  // Loading overlay timing (milliseconds)
  overlayDuration: parseInt(process.env.NEXT_PUBLIC_LOADING_OVERLAY_DURATION || '500', 10),
  fadeDuration: parseInt(process.env.NEXT_PUBLIC_LOADING_FADE_DURATION || '200', 10),
  staggerDelay: parseInt(process.env.NEXT_PUBLIC_STAGGER_DELAY || '100', 10),

  // Debug logging
  debugLogging: process.env.NEXT_PUBLIC_DEBUG_POLLING === 'true',
} as const;

// Type for session state tracking
export interface SessionState {
  wave1_complete: boolean;
  wave2_complete: boolean;
  last_wave1_update: string | null;
  last_wave2_update: string | null;
}

// Helper to log debug messages
export function logPolling(message: string, ...args: any[]) {
  if (POLLING_CONFIG.debugLogging) {
    console.log(`[Polling]`, message, ...args);
  }
}
```

#### 2.3 Refactor usePatientSessions Hook - Add State Tracking

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Lines**: 41-43 (add new refs)

**Add new state tracking:**
```typescript
import { POLLING_CONFIG, SessionState, logPolling } from '@/lib/polling-config';

// Existing refs
const lastWave1Count = useRef<number>(0);
const lastWave2Count = useRef<number>(0);
const lastSessionCount = useRef<number>(0);

// NEW: Track individual session states for change detection
const sessionStatesRef = useRef<Map<string, SessionState>>(new Map());

// NEW: Track current polling interval
const currentIntervalRef = useRef<number>(POLLING_CONFIG.wave1Interval);
```

#### 2.4 Refactor usePatientSessions Hook - Change Detection Logic

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Lines**: 152-217 (replace existing polling effect)

**Replace polling effect with new logic:**
```typescript
useEffect(() => {
  // Don't poll if feature disabled or status is complete
  if (!POLLING_CONFIG.granularUpdatesEnabled || analysisStatus === 'wave2_complete') {
    return;
  }

  logPolling('Starting analysis status polling...');

  const pollStatus = async () => {
    try {
      const status = await demoApiClient.getStatus();

      logPolling('Analysis status:', {
        status: status.analysis_status,
        wave1: status.wave1_complete,
        wave2: status.wave2_complete,
        total: status.session_count
      });

      // Detect which sessions changed
      const changedSessions = detectChangedSessions(status.sessions, sessionStatesRef.current);

      if (changedSessions.length > 0) {
        logPolling(`Progress detected: ${changedSessions.length} session(s) changed`);

        // Update sessions with loading overlays (staggered for polling)
        await updateChangedSessions(changedSessions, setSessionLoading);

        // Update session states ref
        updateSessionStatesRef(status.sessions, sessionStatesRef.current);
      }

      // Update counts
      lastSessionCount.current = status.session_count;
      lastWave1Count.current = status.wave1_complete;
      lastWave2Count.current = status.wave2_complete;

      // Update polling interval based on analysis phase
      const newInterval = determinePollingInterval(status);
      if (newInterval !== currentIntervalRef.current) {
        logPolling(`Switching polling interval: ${currentIntervalRef.current}ms → ${newInterval}ms`);
        currentIntervalRef.current = newInterval;

        // Restart polling with new interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        startPolling(newInterval);
      }

      // Stop polling if Wave 2 complete
      if (status.analysis_status === 'wave2_complete') {
        logPolling('Analysis complete! Stopping polling.');
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    } catch (error) {
      console.error('[Polling] Error fetching status:', error);
    }
  };

  const startPolling = (interval: number) => {
    pollingIntervalRef.current = setInterval(pollStatus, interval);
  };

  // Start initial polling
  startPolling(currentIntervalRef.current);

  // Cleanup
  return () => {
    logPolling('Cleaning up polling interval');
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };
}, [analysisStatus]); // Only re-run if analysisStatus changes
```

#### 2.5 Add Helper Functions for Change Detection

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Location**: Before the hook definition (lines ~100)

**Add utility functions:**
```typescript
/**
 * Determine polling interval based on analysis phase
 */
function determinePollingInterval(status: any): number {
  const { wave1_complete, total, analysis_status } = status;

  // Wave 1 in progress: 1s polling
  if (wave1_complete < total) {
    return POLLING_CONFIG.wave1Interval;
  }

  // Wave 1 complete, Wave 2 not started OR in progress: 3s polling
  if (wave1_complete === total && analysis_status !== 'wave2_complete') {
    return POLLING_CONFIG.wave2Interval;
  }

  // Default to Wave 2 interval
  return POLLING_CONFIG.wave2Interval;
}

/**
 * Detect which sessions changed since last poll
 */
function detectChangedSessions(
  newSessions: any[],
  oldStates: Map<string, SessionState>
): any[] {
  const changed: any[] = [];

  for (const session of newSessions) {
    const oldState = oldStates.get(session.session_id);

    // First time seeing this session
    if (!oldState) {
      if (session.wave1_complete || session.wave2_complete) {
        changed.push(session);
      }
      continue;
    }

    // Check if Wave 1 status changed
    if (!oldState.wave1_complete && session.wave1_complete) {
      changed.push(session);
      continue;
    }

    // Check if Wave 2 status changed
    if (!oldState.wave2_complete && session.wave2_complete) {
      changed.push(session);
      continue;
    }

    // Check if timestamps changed (re-analysis)
    if (session.last_wave1_update && session.last_wave1_update !== oldState.last_wave1_update) {
      changed.push(session);
      continue;
    }

    if (session.last_wave2_update && session.last_wave2_update !== oldState.last_wave2_update) {
      changed.push(session);
      continue;
    }
  }

  return changed;
}

/**
 * Update session states ref with new data
 */
function updateSessionStatesRef(
  sessions: any[],
  statesRef: Map<string, SessionState>
): void {
  for (const session of sessions) {
    statesRef.set(session.session_id, {
      wave1_complete: session.wave1_complete,
      wave2_complete: session.wave2_complete,
      last_wave1_update: session.last_wave1_update,
      last_wave2_update: session.last_wave2_update,
    });
  }
}

/**
 * Update changed sessions with loading overlays (staggered for visual effect)
 */
async function updateChangedSessions(
  changedSessions: any[],
  setSessionLoading: (sessionId: string, loading: boolean) => void
): Promise<void> {
  // Show loading overlays with stagger
  for (let i = 0; i < changedSessions.length; i++) {
    const session = changedSessions[i];
    setTimeout(() => {
      logPolling(`Showing loading overlay for session ${session.session_id}`);
      setSessionLoading(session.session_id, true);
    }, i * POLLING_CONFIG.staggerDelay);
  }

  // Wait for overlay duration + fade
  await new Promise(resolve =>
    setTimeout(resolve, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration)
  );

  // Hide loading overlays
  for (const session of changedSessions) {
    logPolling(`Hiding loading overlay for session ${session.session_id}`);
    setSessionLoading(session.session_id, false);
  }
}
```

#### 2.6 Update SessionDetail for Scroll Preservation

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Lines**: 11-16 (add refs)

**Add scroll refs:**
```typescript
import { useRef, useEffect } from 'react';

export function SessionDetail({ session, onClose }: SessionDetailProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // NEW: Refs for scroll preservation
  const leftColumnRef = useRef<HTMLDivElement>(null);
  const rightColumnRef = useRef<HTMLDivElement>(null);
  const previousSessionIdRef = useRef<string | null>(null);

  const { loadingSessions } = useSessionData();

  // ... rest of component
}
```

#### 2.7 Add Scroll Preservation Logic

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Lines**: After refs definition (~line 40)

**Add scroll preservation effect:**
```typescript
// Preserve scroll position when session updates
useEffect(() => {
  if (!session) return;

  // If session ID changed (user navigated to different session), reset scroll
  if (previousSessionIdRef.current !== session.id) {
    previousSessionIdRef.current = session.id;

    // Reset scroll to top for new session
    if (leftColumnRef.current) leftColumnRef.current.scrollTop = 0;
    if (rightColumnRef.current) rightColumnRef.current.scrollTop = 0;
    return;
  }

  // Same session, preserve scroll position during updates
  const leftScroll = leftColumnRef.current?.scrollTop || 0;
  const rightScroll = rightColumnRef.current?.scrollTop || 0;

  // Restore scroll after React re-renders
  requestAnimationFrame(() => {
    if (leftColumnRef.current) {
      leftColumnRef.current.scrollTo({
        top: leftScroll,
        behavior: 'smooth'
      });
    }
    if (rightColumnRef.current) {
      rightColumnRef.current.scrollTo({
        top: rightScroll,
        behavior: 'smooth'
      });
    }
  });
}, [session?.id, session?.topics, session?.prose_analysis]); // Re-run when data changes
```

#### 2.8 Add refs to scroll containers

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Lines**: 102 and 140 (add refs to divs)

**Left column (line 102):**
```typescript
<div
  ref={leftColumnRef}  // ← ADD THIS
  className="border-r border-[#E0DDD8] dark:border-[#3d3548] overflow-y-auto p-8 bg-[#F8F7F4] dark:bg-[#1a1625]"
>
```

**Right column (line 140):**
```typescript
<div
  ref={rightColumnRef}  // ← ADD THIS
  className="overflow-y-auto p-8 bg-gray-50 dark:bg-[#2a2435]"
>
```

#### 2.9 Create Test Endpoint (Backend)

**File**: `backend/app/routers/demo.py`
**Location**: After existing `/api/demo/status` endpoint (~line 520)

**Add test endpoint:**
```python
@router.post("/test-complete-session/{session_id}")
async def test_complete_session(
    session_id: str,
    wave: int = 1,  # 1 or 2
    db: SupabaseClient = Depends(get_supabase)
):
    """
    TESTING ONLY - REMOVE BEFORE PRODUCTION

    Manually trigger Wave 1 or Wave 2 completion for a session.
    This allows testing granular updates without waiting for real analysis.

    Usage:
    - POST /api/demo/test-complete-session/{session_id}?wave=1
    - POST /api/demo/test-complete-session/{session_id}?wave=2
    """
    try:
        if wave == 1:
            # Simulate Wave 1 completion
            update_data = {
                "topics": ["Test Topic 1", "Test Topic 2"],
                "mood_score": 7.5,
                "summary": "Test summary for manual completion",
                "technique": "CBT - Cognitive Restructuring",
                "action_items": ["Test action item"],
                "topics_extracted_at": datetime.utcnow().isoformat(),
                "mood_analyzed_at": datetime.utcnow().isoformat()
            }
        elif wave == 2:
            # Simulate Wave 2 completion
            update_data = {
                "prose_analysis": "Test prose analysis. This is a manually triggered completion for testing purposes.",
                "deep_analysis": {
                    "progress": {"themes": ["test"]},
                    "insights": {"patterns": ["test"]},
                    "skills": {"demonstrated": ["test"]},
                    "relationship": {"quality": "strong"},
                    "recommendations": {"focus_areas": ["test"]}
                },
                "prose_generated_at": datetime.utcnow().isoformat(),
                "deep_analyzed_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Wave must be 1 or 2")

        # Update session
        response = (
            db.table("therapy_sessions")
            .update(update_data)
            .eq("id", session_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "session_id": session_id,
            "wave": wave,
            "message": f"Session manually completed for Wave {wave}"
        }

    except Exception as e:
        print(f"Error in test endpoint: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Success Criteria

#### Automated Verification:
- [ ] Frontend builds without errors: `cd frontend && npm run build`
- [ ] TypeScript compilation passes: `cd frontend && npm run type-check`
- [ ] Linting passes: `cd frontend && npm run lint`
- [ ] Environment variables load correctly (check console logs)
- [ ] Polling starts at 1s interval during Wave 1
- [ ] Polling switches to 3s interval after Wave 1 completes
- [ ] Polling stops when Wave 2 completes

#### Manual Verification:
- [ ] Hard refresh → Demo init → Sessions load with 1s polling
- [ ] Use test endpoint to complete Session #1 Wave 1 → Only card #1 shows loading overlay
- [ ] Use test endpoint to complete Session #2 Wave 1 → Only card #2 shows loading overlay
- [ ] Use test endpoint to complete multiple sessions → Cards show staggered loading overlays (100ms delay)
- [ ] Observe polling interval switch from 1s → 3s after Wave 1 complete
- [ ] Open SessionDetail for Session #3 → Complete Session #5 Wave 1 → Detail page doesn't refresh
- [ ] Scroll down in SessionDetail → Update that session → Scroll position preserved with smooth animation
- [ ] Wave 2 completes → Polling stops, console shows "Stopping polling"

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Backend - Database-Backed SSE Event Queue

### Overview
Create a database-backed event queue to replace the in-memory `PipelineLogger._event_queue`. This fixes the subprocess isolation bug where events written in seed scripts never reach the FastAPI SSE endpoint.

### Changes Required

#### 3.1 Create Database Migration

**File**: `backend/supabase/migrations/013_add_pipeline_events_table.sql` (NEW FILE)
**Purpose**: Create `pipeline_events` table for cross-process event storage

```sql
-- Migration: Add pipeline_events table for SSE event queue
-- Date: 2026-01-03
-- Description: Database-backed event queue to fix subprocess isolation bug

CREATE TABLE pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL,
  session_id UUID NULL,
  session_date VARCHAR(50),
  phase VARCHAR(20) NOT NULL,        -- 'WAVE1' | 'WAVE2' | 'TRANSCRIPT'
  event VARCHAR(50) NOT NULL,        -- 'START' | 'PROGRESS' | 'COMPLETE' | 'ERROR'
  status VARCHAR(20) NOT NULL,       -- 'success' | 'error'
  message TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  consumed BOOLEAN DEFAULT FALSE,    -- SSE marks as consumed after sending

  -- Foreign key (optional, allows orphaned events if patient deleted)
  CONSTRAINT fk_patient FOREIGN KEY (patient_id)
    REFERENCES patients(id) ON DELETE CASCADE,

  -- Foreign key (optional, allows events without session)
  CONSTRAINT fk_session FOREIGN KEY (session_id)
    REFERENCES therapy_sessions(id) ON DELETE CASCADE
);

-- Index for efficient SSE queries (patient_id + unconsumed events)
CREATE INDEX idx_pipeline_events_patient_unconsumed
  ON pipeline_events(patient_id, created_at)
  WHERE consumed = FALSE;

-- Index for cleanup queries (old consumed events)
CREATE INDEX idx_pipeline_events_consumed
  ON pipeline_events(consumed, created_at);

-- Comments for clarity
COMMENT ON TABLE pipeline_events IS 'Cross-process event queue for SSE real-time updates';
COMMENT ON COLUMN pipeline_events.consumed IS 'Marks event as sent to frontend via SSE';
COMMENT ON COLUMN pipeline_events.phase IS 'Analysis phase: WAVE1 (topics/mood), WAVE2 (deep/prose), TRANSCRIPT (loading)';
COMMENT ON COLUMN pipeline_events.event IS 'Event type: START, PROGRESS, COMPLETE, ERROR';
COMMENT ON COLUMN pipeline_events.metadata IS 'Additional event data (JSON format)';
```

#### 3.2 Apply Migration via Supabase MCP

**Action**: Execute migration using Supabase MCP tool

```typescript
// This will be done via MCP during implementation
await mcp__supabase__apply_migration({
  name: "add_pipeline_events_table",
  query: /* SQL from 013_add_pipeline_events_table.sql */
});
```

**Manual verification**:
```bash
# Check table exists
psql> \dt pipeline_events

# Check indices
psql> \di pipeline_events*

# Verify structure
psql> \d pipeline_events
```

#### 3.3 Add Environment Variable for Retry Mode

**File**: `backend/.env.example`
**Add:**
```bash
# Pipeline Event Logging Configuration
PIPELINE_EVENT_RETRY_MODE=development  # 'development' | 'production'
```

**File**: `backend/.env`
**Add:**
```bash
PIPELINE_EVENT_RETRY_MODE=development
```

#### 3.4 Refactor PipelineLogger - Add Database Writes

**File**: `backend/app/services/pipeline_logger.py`
**Lines**: ~50-100 (modify `log_event` method)

**Current implementation:**
```python
def log_event(self, event: str, status: str, message: str = "", metadata: dict = None):
    """Log pipeline event to in-memory queue"""
    event_data = {
        "patient_id": self.patient_id,
        "session_id": self.session_id,
        "session_date": self.session_date,
        "phase": self.phase.value,
        "event": event,
        "status": status,
        "message": message,
        "metadata": metadata or {}
    }

    # Add to in-memory queue
    if self.patient_id not in PipelineLogger._event_queue:
        PipelineLogger._event_queue[self.patient_id] = []
    PipelineLogger._event_queue[self.patient_id].append(event_data)
```

**Refactored implementation:**
```python
import os
from datetime import datetime
import asyncio

def log_event(self, event: str, status: str, message: str = "", metadata: dict = None):
    """Log pipeline event to database (with in-memory fallback)"""
    event_data = {
        "patient_id": self.patient_id,
        "session_id": self.session_id,
        "session_date": self.session_date,
        "phase": self.phase.value,
        "event": event,
        "status": status,
        "message": message,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }

    # Try database write (with retries in development mode)
    retry_mode = os.getenv("PIPELINE_EVENT_RETRY_MODE", "production")
    max_retries = 3 if retry_mode == "development" else 0

    success = self._write_to_database(event_data, max_retries)

    if not success:
        # Fallback: Add to in-memory queue
        print(f"[PipelineLogger] Database write failed, using in-memory fallback", flush=True)
        if self.patient_id not in PipelineLogger._event_queue:
            PipelineLogger._event_queue[self.patient_id] = []
        PipelineLogger._event_queue[self.patient_id].append(event_data)

def _write_to_database(self, event_data: dict, max_retries: int) -> bool:
    """Write event to database with retry logic"""
    from app.database import get_supabase

    for attempt in range(max_retries + 1):
        try:
            db = get_supabase()

            # Insert event
            response = db.table("pipeline_events").insert({
                "patient_id": event_data["patient_id"],
                "session_id": event_data.get("session_id"),
                "session_date": event_data.get("session_date"),
                "phase": event_data["phase"],
                "event": event_data["event"],
                "status": event_data["status"],
                "message": event_data.get("message", ""),
                "metadata": event_data.get("metadata", {}),
                "consumed": False
            }).execute()

            if response.data:
                print(f"[PipelineLogger] Event logged to database: {event_data['phase']} {event_data['event']}", flush=True)
                return True
            else:
                print(f"[PipelineLogger] Database insert returned no data (attempt {attempt + 1}/{max_retries + 1})", flush=True)

        except Exception as e:
            print(f"[PipelineLogger] Database write error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}", flush=True)

            if attempt < max_retries:
                # Wait before retry (exponential backoff)
                import time
                wait_time = 0.1 * (2 ** attempt)  # 0.1s, 0.2s, 0.4s
                time.sleep(wait_time)

    return False
```

#### 3.5 Update SSE Endpoint to Read from Database

**File**: `backend/app/routers/sse.py`
**Lines**: 35-80 (replace event queue logic)

**Current implementation:**
```python
async def stream_events(patient_id: str, request: Request):
    """Stream pipeline events for a patient"""

    async def event_generator():
        last_index = 0

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Get events from in-memory queue
            events = PipelineLogger.get_events(patient_id)

            # Send new events
            if len(events) > last_index:
                for event in events[last_index:]:
                    yield f"data: {json.dumps(event)}\n\n"
                last_index = len(events)

            # Keep-alive ping
            yield f": keepalive\n\n"

            await asyncio.sleep(0.5)
```

**Refactored implementation:**
```python
from app.database import get_supabase

async def stream_events(patient_id: str, request: Request):
    """Stream pipeline events for a patient from database"""

    async def event_generator():
        last_event_id = None

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                print(f"[SSE] Client disconnected for patient {patient_id}", flush=True)
                break

            try:
                db = get_supabase()

                # Query unconsumed events for this patient
                query = (
                    db.table("pipeline_events")
                    .select("*")
                    .eq("patient_id", patient_id)
                    .eq("consumed", False)
                    .order("created_at", desc=False)
                )

                # If we've seen events before, only get newer ones
                if last_event_id:
                    query = query.gt("created_at", last_event_id)

                response = query.execute()
                events = response.data or []

                # Send new events
                for event in events:
                    event_data = {
                        "patient_id": event["patient_id"],
                        "session_id": event.get("session_id"),
                        "session_date": event.get("session_date"),
                        "phase": event["phase"],
                        "event": event["event"],
                        "status": event["status"],
                        "message": event.get("message", ""),
                        "metadata": event.get("metadata", {})
                    }

                    yield f"data: {json.dumps(event_data)}\n\n"

                    # Mark event as consumed
                    db.table("pipeline_events").update({
                        "consumed": True
                    }).eq("id", event["id"]).execute()

                    # Update last seen event timestamp
                    last_event_id = event["created_at"]

                    print(f"[SSE] Sent event to patient {patient_id}: {event['phase']} {event['event']}", flush=True)

                # Keep-alive ping
                yield f": keepalive\n\n"

            except Exception as e:
                print(f"[SSE] Error querying events: {str(e)}", flush=True)
                # Continue polling despite errors

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### Success Criteria

#### Automated Verification:
- [ ] Migration applies successfully via Supabase MCP
- [ ] `pipeline_events` table exists in database
- [ ] Indices created correctly (`idx_pipeline_events_patient_unconsumed`, `idx_pipeline_events_consumed`)
- [ ] Backend starts without errors after PipelineLogger refactor
- [ ] Seed script writes events to database (check with SQL query)
- [ ] SSE endpoint reads events from database (check Railway logs)

#### Manual Verification:
- [ ] Run seed script → Check `pipeline_events` table → Events exist with `consumed = false`
- [ ] Connect SSE in browser → Events sent → Check database → Events marked `consumed = true`
- [ ] Railway logs show: `[PipelineLogger] Event logged to database: WAVE1 COMPLETE`
- [ ] Railway logs show: `[SSE] Sent event to patient {id}: WAVE1 COMPLETE`
- [ ] Disconnect SSE → Reconnect → Only new events sent (no duplicates)
- [ ] Simulate database failure → Events fall back to in-memory queue (check logs)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 4: Frontend SSE Integration + Testing + Documentation

### Overview
Integrate SSE with granular polling updates, remove test endpoint, perform comprehensive testing, and update all documentation to reflect "TheraBridge" naming.

### Changes Required

#### 4.1 Update WaveCompletionBridge for No-Stagger SSE Updates

**File**: `frontend/app/patient/components/WaveCompletionBridge.tsx`
**Lines**: 94-129 (modify SSE callbacks)

**Current implementation:**
```typescript
onWave1SessionComplete: async (sessionId, sessionDate) => {
  console.log(`🔄 Wave 1 complete for ${sessionDate}! Showing loading state...`);
  setSessionLoading(sessionId, true);
  await new Promise(resolve => setTimeout(resolve, 100));
  await refresh();
  setSessionLoading(sessionId, false);
}
```

**Refactored implementation (no stagger for real-time SSE):**
```typescript
import { POLLING_CONFIG, logPolling } from '@/lib/polling-config';

onWave1SessionComplete: async (sessionId, sessionDate) => {
  if (!POLLING_CONFIG.sseEnabled) {
    logPolling('[SSE] SSE disabled via feature flag, ignoring event');
    return;
  }

  logPolling(`[SSE] Wave 1 complete for session ${sessionDate} (${sessionId})`);

  // Show loading overlay immediately (no stagger for real-time)
  setSessionLoading(sessionId, true);

  // Fetch updated session data
  await refresh();

  // Hide loading overlay after duration + fade
  setTimeout(() => {
    setSessionLoading(sessionId, false);
  }, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration);
},

onWave2SessionComplete: async (sessionId, sessionDate) => {
  if (!POLLING_CONFIG.sseEnabled) {
    logPolling('[SSE] SSE disabled via feature flag, ignoring event');
    return;
  }

  logPolling(`[SSE] Wave 2 complete for session ${sessionDate} (${sessionId})`);

  // Show loading overlay immediately (no stagger for real-time)
  setSessionLoading(sessionId, true);

  // Fetch updated session data
  await refresh();

  // Hide loading overlay after duration + fade
  setTimeout(() => {
    setSessionLoading(sessionId, false);
  }, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration);
}
```

#### 4.2 Update Polling to Respect SSE Feature Flag

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Lines**: 152 (modify polling effect condition)

**Current:**
```typescript
useEffect(() => {
  if (!POLLING_CONFIG.granularUpdatesEnabled || analysisStatus === 'wave2_complete') {
    return;
  }
  // ... polling logic
}, [analysisStatus]);
```

**Updated (SSE takes priority):**
```typescript
useEffect(() => {
  // If SSE enabled, disable polling (SSE will handle real-time updates)
  if (POLLING_CONFIG.sseEnabled) {
    logPolling('SSE enabled, polling disabled');
    return;
  }

  // If granular updates disabled or analysis complete, stop polling
  if (!POLLING_CONFIG.granularUpdatesEnabled || analysisStatus === 'wave2_complete') {
    return;
  }

  // ... polling logic
}, [analysisStatus]);
```

#### 4.3 Remove Test Endpoint

**File**: `backend/app/routers/demo.py`
**Lines**: ~520 (delete entire test endpoint)

**Action**: Delete the `/test-complete-session/{session_id}` endpoint added in Phase 2

```python
# DELETE THIS ENTIRE FUNCTION:
# @router.post("/test-complete-session/{session_id}")
# async def test_complete_session(...):
#     ...
```

#### 4.4 Update Frontend Environment Variables for Production

**File**: `frontend/.env.local`
**Changes**: Set production-ready defaults

```bash
# Granular Updates Feature Flags
NEXT_PUBLIC_GRANULAR_UPDATES=true          # ✅ Enable per-session updates
NEXT_PUBLIC_SSE_ENABLED=false              # ⚠️ Keep disabled until verified in production

# Polling Configuration (fallback when SSE disabled)
NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000    # 1s during Wave 1
NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000    # 3s during Wave 2

# Loading Overlay Timing
NEXT_PUBLIC_LOADING_OVERLAY_DURATION=500   # 500ms spinner
NEXT_PUBLIC_LOADING_FADE_DURATION=200      # 200ms fade-out
NEXT_PUBLIC_STAGGER_DELAY=100              # 100ms delay between batch updates

# Debug Logging
NEXT_PUBLIC_DEBUG_POLLING=false            # ⚠️ Disable for production
```

#### 4.5 Update CLAUDE.md

**File**: `.claude/CLAUDE.md`
**Lines**: 109-141 (update Current Focus section)

**Replace with:**
```markdown
## Current Focus: Real-Time Granular Session Updates - COMPLETE ✅

**Implementation Complete (2026-01-03):**
- ✅ Backend `/api/demo/status` enhanced with full analysis data per session
- ✅ Frontend granular polling with per-session loading overlays
- ✅ Adaptive polling: 1s during Wave 1 → 3s during Wave 2 → stop
- ✅ Database-backed SSE event queue (fixes subprocess isolation bug)
- ✅ SSE integration with feature flags (disabled by default)
- ✅ SessionDetail scroll preservation with smooth animation
- ✅ Test endpoint removed, documentation updated

**Production Behavior:**
1. **Demo Init (0-3s)**: Demo initialized, patient ID stored, polling starts at 1s
2. **Transcripts Loading (0-30s)**: Sessions endpoint may timeout, polling detects sessions
3. **Wave 1 Complete (~60s)**: Individual cards show loading overlay as each session completes
4. **Polling Switch**: Automatically switches to 3s interval after Wave 1 complete
5. **Wave 2 Complete (~9.6 min)**: Individual cards update with prose analysis, polling stops
6. **SSE Support**: Real-time events via database queue (enable with `NEXT_PUBLIC_SSE_ENABLED=true`)

**Feature Flags:**
- `NEXT_PUBLIC_GRANULAR_UPDATES=true` - Per-session updates enabled
- `NEXT_PUBLIC_SSE_ENABLED=false` - SSE disabled (polling fallback active)
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000` - 1s during Wave 1
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000` - 3s during Wave 2

**Next Steps:**
1. Monitor production logs for granular update behavior
2. Enable SSE in production once verified (`NEXT_PUBLIC_SSE_ENABLED=true`)
3. Implement Feature 2: Analytics Dashboard
```

**Also update all references:**
- Find and replace: `TherapyBridge` → `TheraBridge`
- Update: `Project MDs/TherapyBridge.md` → `Project MDs/TheraBridge.md`

#### 4.6 Update SESSION_LOG.md

**File**: `.claude/SESSION_LOG.md`
**Lines**: After line 148 (update status)

**Update existing entry:**
```markdown
**Status:** ✅ COMPLETE - All phases implemented and tested

**Commits:**
- `XXXXXXX` - Phase 1: Backend delta data enhancement
- `XXXXXXX` - Phase 2: Frontend granular polling updates
- `XXXXXXX` - Phase 3: Database-backed SSE event queue
- `XXXXXXX` - Phase 4: SSE integration + documentation updates
```

#### 4.7 Update TheraBridge.md (formerly TherapyBridge.md)

**File**: `Project MDs/TheraBridge.md`
**Action**: Rename file and update all references

```bash
# Rename file
mv "Project MDs/TherapyBridge.md" "Project MDs/TheraBridge.md"

# Update content with new features
```

**Add section to TheraBridge.md:**
```markdown
## Real-Time Session Updates (Implemented 2026-01-03)

**Feature:** Per-session granular updates with loading overlays

**User Experience:**
- Individual session cards show loading overlay (500ms spinner + 200ms fade) only when that specific session completes analysis
- Polling adapts to analysis phase: 1s during Wave 1 → 3s during Wave 2
- SessionDetail page only updates if viewing session that changed
- Scroll position preserved during updates with smooth animation
- SSE provides instant updates (polling as fallback)

**Technical Implementation:**
- Backend `/api/demo/status` returns full analysis data per session (topics, mood_score, summary, prose_analysis)
- Frontend tracks session state via `Map<sessionId, state>` for O(1) change detection
- Adaptive polling intervals configured via environment variables
- Database-backed SSE event queue (`pipeline_events` table) fixes subprocess isolation bug
- Feature flags allow safe rollout: `NEXT_PUBLIC_GRANULAR_UPDATES`, `NEXT_PUBLIC_SSE_ENABLED`

**Configuration:**
```bash
# Frontend (.env.local)
NEXT_PUBLIC_GRANULAR_UPDATES=true          # Enable per-session updates
NEXT_PUBLIC_SSE_ENABLED=false              # Enable SSE (disabled until verified)
NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000    # 1s during Wave 1
NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000    # 3s during Wave 2

# Backend (.env)
PIPELINE_EVENT_RETRY_MODE=development      # 'development' | 'production'
```

**Files Modified:**
- Backend: `app/routers/demo.py`, `app/services/pipeline_logger.py`, `app/routers/sse.py`
- Frontend: `lib/polling-config.ts`, `app/patient/lib/usePatientSessions.ts`, `app/patient/components/SessionDetail.tsx`, `app/patient/components/WaveCompletionBridge.tsx`
- Database: `supabase/migrations/013_add_pipeline_events_table.sql`
```

### Success Criteria

#### Automated Verification:
- [ ] Backend builds without test endpoint: `cd backend && uvicorn app.main:app --reload`
- [ ] Frontend builds for production: `cd frontend && npm run build`
- [ ] All TypeScript types valid: `cd frontend && npm run type-check`
- [ ] No linting errors: `cd frontend && npm run lint`
- [ ] SSE connects when `NEXT_PUBLIC_SSE_ENABLED=true`
- [ ] Polling disabled when SSE enabled
- [ ] Polling active when SSE disabled

#### Manual Verification:
- [ ] **Granular Polling (SSE disabled):**
  - [ ] Hard refresh → Sessions load → Polling at 1s
  - [ ] Wave 1 Session #1 completes → Only card #1 shows loading overlay
  - [ ] Multiple sessions complete together → Staggered loading overlays (100ms delay)
  - [ ] Polling switches to 3s after Wave 1 complete
  - [ ] Wave 2 sessions complete → Individual cards update with 3s polling
  - [ ] SessionDetail open → Other sessions update → Detail doesn't refresh
  - [ ] SessionDetail viewing session that updates → Scroll preserved smoothly

- [ ] **SSE Real-Time (SSE enabled):**
  - [ ] Hard refresh → SSE connects successfully
  - [ ] Wave 1 Session #1 completes → Instant loading overlay (no stagger)
  - [ ] Wave 2 Session #1 completes → Instant prose update
  - [ ] Railway logs show events sent: `[SSE] Sent event to patient {id}: WAVE1 COMPLETE`
  - [ ] Database shows events consumed: `SELECT * FROM pipeline_events WHERE consumed = true`
  - [ ] No polling requests in network tab (SSE takes over)

- [ ] **Feature Flag Testing:**
  - [ ] Set `NEXT_PUBLIC_GRANULAR_UPDATES=false` → Behavior reverts to old bulk refresh
  - [ ] Set `NEXT_PUBLIC_SSE_ENABLED=true` → Polling stops, SSE active
  - [ ] Set `NEXT_PUBLIC_SSE_ENABLED=false` → Polling resumes, SSE inactive

- [ ] **Documentation:**
  - [ ] All references to "TherapyBridge" changed to "TheraBridge"
  - [ ] CLAUDE.md reflects completed implementation
  - [ ] SESSION_LOG.md marked as complete with commit hashes
  - [ ] TheraBridge.md includes new feature documentation

**Implementation Note**: After completing this phase and all automated verification passes, perform comprehensive manual testing across all scenarios. Once confirmed working, this implementation is complete and ready for production deployment.

---

## Testing Strategy

### Unit Tests
**Scope:** Individual utility functions
- `determinePollingInterval()` - returns correct interval based on status
- `detectChangedSessions()` - identifies which sessions changed
- `updateSessionStatesRef()` - updates Map correctly

### Integration Tests
**Scope:** End-to-end flows
- Demo initialization → Sessions load → Wave 1 polling → Wave 2 polling → Stop
- SSE connection → Event received → UI updates
- Polling fallback when SSE fails
- Feature flag behavior (granular enabled/disabled, SSE enabled/disabled)

### Manual Testing Steps

#### Test 1: Granular Polling (SSE Disabled)
```bash
# Setup
NEXT_PUBLIC_GRANULAR_UPDATES=true
NEXT_PUBLIC_SSE_ENABLED=false
NEXT_PUBLIC_DEBUG_POLLING=true

# Steps
1. Hard refresh browser
2. Observe polling logs: "Starting analysis status polling..."
3. Wait for Session #1 Wave 1 complete
4. Verify: Only card #1 shows loading overlay
5. Verify: Console shows "Showing loading overlay for session {id}"
6. Verify: Polling interval is 1000ms
7. Wait for all Wave 1 complete
8. Verify: Console shows "Switching polling interval: 1000ms → 3000ms"
9. Verify: Polling continues at 3000ms
10. Wait for Wave 2 complete
11. Verify: Console shows "Analysis complete! Stopping polling."
12. Verify: No more polling requests in network tab
```

#### Test 2: SSE Real-Time Updates (SSE Enabled)
```bash
# Setup
NEXT_PUBLIC_GRANULAR_UPDATES=true
NEXT_PUBLIC_SSE_ENABLED=true
NEXT_PUBLIC_DEBUG_POLLING=true

# Steps
1. Hard refresh browser
2. Observe SSE connection in network tab (EventSource)
3. Verify: Console shows "SSE enabled, polling disabled"
4. Verify: No polling requests in network tab
5. Wait for Session #1 Wave 1 complete
6. Verify: Railway logs show "[SSE] Sent event to patient {id}: WAVE1 COMPLETE"
7. Verify: Frontend logs show "[SSE] Wave 1 complete for session..."
8. Verify: Only card #1 shows loading overlay (no stagger)
9. Check database: `SELECT * FROM pipeline_events WHERE consumed = true`
10. Verify: Event marked as consumed
11. Disconnect SSE → Reconnect
12. Verify: Only new events sent (no duplicates)
```

#### Test 3: SessionDetail Scroll Preservation
```bash
# Steps
1. Open SessionDetail for Session #3
2. Scroll to bottom of left column (transcript)
3. Scroll to middle of right column (analysis)
4. Trigger Session #3 Wave 2 update (wait for completion)
5. Verify: Prose analysis appears in right column
6. Verify: Left column scroll position unchanged
7. Verify: Right column scroll position preserved (smooth animation back to position)
8. Verify: No jarring jumps or content shifts
```

#### Test 4: Feature Flag Rollback
```bash
# Test granular updates disabled
NEXT_PUBLIC_GRANULAR_UPDATES=false

# Steps
1. Hard refresh
2. Wait for Wave 1 complete
3. Verify: ALL sessions refresh at once (old behavior)
4. Verify: No individual loading overlays

# Test SSE disabled (polling fallback)
NEXT_PUBLIC_SSE_ENABLED=false

# Steps
1. Hard refresh
2. Verify: Polling starts
3. Verify: No SSE connection in network tab
4. Wait for Session #1 complete
5. Verify: Polling detects change, shows loading overlay
```

#### Test 5: Staggered vs Instant Loading
```bash
# Polling (batch detection)
NEXT_PUBLIC_SSE_ENABLED=false

# Steps
1. Hard refresh
2. Wait for multiple sessions to complete between polls (e.g., 3 sessions)
3. Verify: Cards #1, #2, #3 light up in sequence (100ms stagger)
4. Verify: Visual "cascade" effect

# SSE (real-time)
NEXT_PUBLIC_SSE_ENABLED=true

# Steps
1. Hard refresh
2. Wait for Session #1 complete
3. Verify: Card #1 lights up instantly (no stagger)
4. Wait for Session #2 complete
5. Verify: Card #2 lights up instantly (separate from #1)
```

## Performance Considerations

### Polling Efficiency
- **Wave 1**: 1s polling for ~60 seconds = ~60 requests
- **Wave 2**: 3s polling for ~9.6 minutes = ~192 requests
- **Total**: ~252 polling requests per demo session
- **Optimization**: SSE eliminates polling entirely (0 requests when enabled)

### Database Load
- **SSE queries**: `SELECT` on indexed `pipeline_events` table, filtered by `patient_id` + `consumed = false`
- **Index efficiency**: Query hits `idx_pipeline_events_patient_unconsumed` (very fast)
- **Event cleanup**: Periodically delete old consumed events (e.g., daily cron job)

### Frontend State Management
- **Map lookups**: O(1) for session state comparison
- **Memory footprint**: ~10 sessions × ~200 bytes = ~2KB per demo
- **Re-render optimization**: React.memo on SessionCard prevents unnecessary re-renders

### Network Bandwidth
- **Polling**: ~500 bytes per request × 252 requests = ~126KB per demo
- **SSE**: ~200 bytes per event × 20 events = ~4KB per demo (95% reduction)

## Migration Notes

### Database Migration
- Run `013_add_pipeline_events_table.sql` via Supabase MCP
- No data migration needed (new table)
- Foreign keys allow cascading deletes (cleanup automatic)

### Frontend Migration
- Environment variables backward compatible (defaults to old behavior if not set)
- Feature flags allow gradual rollout:
  1. Deploy with `GRANULAR_UPDATES=true`, `SSE_ENABLED=false` (polling fallback)
  2. Monitor for issues
  3. Enable SSE: `SSE_ENABLED=true`
  4. Monitor for SSE events in Railway logs
  5. If issues, rollback: `SSE_ENABLED=false`

### Backend Migration
- PipelineLogger backward compatible (falls back to in-memory if database fails)
- No code changes needed in seed scripts (PipelineLogger interface unchanged)
- Environment variable `PIPELINE_EVENT_RETRY_MODE` controls retry behavior

### Rollback Plan
If issues arise post-deployment:
1. **Immediate**: Set `NEXT_PUBLIC_SSE_ENABLED=false` (revert to polling)
2. **Next**: Set `NEXT_PUBLIC_GRANULAR_UPDATES=false` (revert to bulk refresh)
3. **Nuclear**: Redeploy previous commit (no database changes needed, table just unused)

## References

- Original issue tracking: `.claude/SESSION_LOG.md` (2026-01-03 entry)
- Related research: Railway logs (2026-01-03 05:46)
- Database schema: `backend/supabase/migrations/013_add_pipeline_events_table.sql`
- Frontend implementation: `frontend/lib/polling-config.ts`, `frontend/app/patient/lib/usePatientSessions.ts`
- Backend implementation: `backend/app/services/pipeline_logger.py`, `backend/app/routers/sse.py`
