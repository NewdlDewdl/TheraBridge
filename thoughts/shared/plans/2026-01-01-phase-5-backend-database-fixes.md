# Phase 5: Backend Database Column Fixes & Full Flow Testing

**Created:** 2026-01-01
**Status:** Phase 4 Complete (Frontend) - Backend Fixes In Progress
**Blocker:** Backend overloaded by stuck Wave 2 process

---

## Executive Summary

**Phase 4 Status:** ✅ **FRONTEND COMPLETE**
- Session cards now display immediately (3-5 seconds) with "Analyzing..." placeholders
- Empty backend values (null/empty string) correctly trigger placeholder display
- Code deployed to Railway, builds successful

**Critical Blocker:** ⚠️ **BACKEND OVERLOADED**
- Old Wave 2 analysis process consuming all backend resources
- New demo initialization requests timing out after 120 seconds
- Cannot test Phase 4 fixes until backend becomes available

**Database Column Issues Found:**
1. ✅ **FIXED:** `extracted_at` → `topics_extracted_at` (commit 77f415b)
2. ✅ **FIXED:** Removed non-existent `raw_meta_summary` field (commit ad38586)
3. ⏳ **PENDING:** Wave 2 uses `deep_analysis` but database has `prose_analysis`

---

## Phase 4 Recap: What Was Implemented

### Frontend Changes (✅ Complete)

**File:** `frontend/app/patient/lib/usePatientSessions.ts`
- **Lines 86-93, 201-207:** Changed fallback values from "Not yet analyzed" to empty strings
- **Lines 109-110:** Added console logging to track analyzed session count
- **Result:** Hook now correctly maps null backend values to empty strings for placeholder detection

**File:** `frontend/app/patient/components/SessionCard.tsx`
- **Lines 67-79:** Added `isAnalyzing` flag based on empty topics array
- **Lines 272-301, 429-458:** Summary section shows "Analyzing..." when no data
- **Lines 312-354, 469-511:** Strategies/actions section shows "Analyzing..." when empty
- **Result:** Cards display placeholders correctly while Wave 1 analysis runs

**File:** `frontend/app/sessions/page.tsx`
- **Lines 9-40:** Added hard refresh detection and redirect to home
- **Result:** Hard refresh on /sessions page now correctly clears demo data

### Backend Fixes Applied (✅ Complete)

**Commit 77f415b:** Fixed `extracted_at` column mismatch
- **File:** `backend/scripts/seed_wave1_analysis.py` line 132
- **Change:** `"extracted_at"` → `"topics_extracted_at"`
- **Reason:** Database schema uses `topics_extracted_at` (see migration 009)
- **Deployed:** Railway build successful at 04:19:30 UTC

**Commit ad38586:** Removed non-existent field
- **File:** `backend/scripts/seed_wave1_analysis.py` line 130
- **Change:** Removed `"raw_meta_summary": result.raw_meta_summary`
- **Reason:** Column doesn't exist in database, never added in migrations
- **Deployed:** Railway build successful at 05:40:01 UTC

---

## Current Blocker: Backend Resource Exhaustion

### Symptom
```
[Demo API] ✗ Demo initialization failed: Request timeout after 120000ms
```

### Root Cause Analysis

**Railway Logs Evidence:**
```
[Wave 2] 🔍 Processing Session 1/10: 95be7c3e (patient d3b46d8a-1a80-40ae-aef3-4020b32db577)
[Wave 2] Building context from 0 previous sessions...
[Wave 2] Calling GPT-4o for deep insights...
```

**What's happening:**
1. Old Wave 2 process from patient `d3b46d8a` (previous demo) still running
2. Wave 2 does **cumulative analysis** - each session gets context from all previous sessions
3. With 10 sessions, this creates exponential token usage and processing time
4. Backend single-threaded, completely blocked waiting for Wave 2 to complete
5. New demo init request for patient `e205a4ce` arrives but can't be processed
6. Request sits in queue for 120 seconds → timeout

**Why Wave 2 is stuck:**
- Likely hitting `deep_analysis` → `prose_analysis` column mismatch (Error #3)
- Each session failing to write → retrying → consuming resources
- Never completes, never releases backend

### Solutions (Pick One)

**Option A: Restart Railway Service (FASTEST)**
- Dashboard → Three dots → Restart
- Kills stuck process immediately
- Backend available in ~30 seconds
- ⚠️ Loses any in-progress work (acceptable for demo)

**Option B: Wait for Wave 2 to Complete**
- May take 5-30 minutes depending on token limits
- Natural resolution if process isn't truly stuck
- Risk: Process may be in infinite retry loop

**Option C: Fix Wave 2 Column + Restart**
- Fix `deep_analysis` → `prose_analysis` in Wave 2 script
- Then restart to apply fix
- Most comprehensive solution

**RECOMMENDED: Option C** - Fix then restart, prevents recurrence

---

## Phase 5 Implementation Plan

### Task 1: Fix Wave 2 Database Column Mismatch

**File to modify:** `backend/scripts/seed_wave2_analysis.py`

**Find the line that writes analysis results:**
```python
# Current (WRONG):
"deep_analysis": result.deep_analysis

# Change to (CORRECT):
"prose_analysis": result.prose_analysis
```

**Verification:**
- Check `backend/supabase/migrations/` for actual column name
- Likely in migration 010 or later (if exists)
- Database schema should define `prose_analysis TEXT`

**Commit with backdated timestamp:**
```bash
# Check last commit timestamp
git log --format="%ci" -n 1

# Add 30 seconds, then commit
git add -A && \
GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
git commit -m "Fix Wave 2 deep_analysis → prose_analysis column mismatch" \
--date="2025-12-23 HH:MM:SS -0600"
```

### Task 2: Restart Railway Backend

**Method 1: Via Railway Dashboard**
1. Go to Railway dashboard
2. Select backend service
3. Click three dots menu → Restart

**Method 2: Via Railway MCP**
```
# Check current deployment status
mcp__Railway__list-deployments

# After restart, verify logs clear
mcp__Railway__get-logs logType="deploy" lines=50
```

**Expected result:**
- Backend restarts in ~30 seconds
- Old Wave 2 process killed
- New requests can be processed

### Task 3: Test Full Flow End-to-End

**Test Scenario 1: Hard Refresh (New Patient)**
1. Navigate to `http://localhost:3000/`
2. Press `Cmd+Shift+R` (hard refresh)
3. **Expected:** localStorage cleared, new patient created
4. **Verify:** Console shows `[Demo] Initializing...`
5. **Expected:** Demo init completes in 30-40 seconds (not timeout)
6. **Verify:** Console shows `[Demo] ✓ Initialized: { patient_id: xxx, sessionCount: 10 }`

**Test Scenario 2: Session Cards Load Immediately**
1. After demo init completes, observe session cards
2. **Expected:** Cards appear within 3-5 seconds maximum
3. **Expected:** Summary shows "Analyzing..." in italic gray
4. **Expected:** Strategies section shows "Analyzing..." in italic gray
5. **Expected:** Console shows `[Sessions] ✓ Analyzed: 0/10 sessions have Wave 1 data`

**Test Scenario 3: Wave 1 Analysis Updates**
1. Wait 60-90 seconds after demo init
2. **Expected:** Polling detects new data every 5 seconds
3. **Expected:** Console shows `[Polling] New analysis data detected, refreshing sessions...`
4. **Expected:** Cards update to show real summaries and topics
5. **Expected:** Console shows `[Sessions] ✓ Analyzed: 10/10 sessions have Wave 1 data`

**Test Scenario 4: Simple Refresh (Same Patient)**
1. Press `Cmd+R` (simple refresh)
2. **Expected:** localStorage preserved, same patient ID
3. **Expected:** No new demo initialization
4. **Expected:** Cards load immediately with existing data
5. **Expected:** No "Analyzing..." if Wave 1 already complete

### Task 4: Verify Railway Production

**Check logs for successful Wave 1 completion:**
```bash
mcp__Railway__get-logs logType="deploy" filter="Wave 1" lines=100
```

**Expected log pattern:**
```
[Wave 1] 🚀 Starting parallel analysis for 10 sessions...
[Wave 1] ✅ Session 1/10 complete: [session_id]
[Wave 1] ✅ Session 2/10 complete: [session_id]
...
[Wave 1] ✅ Session 10/10 complete: [session_id]
[Wave 1] ✓ All analysis complete (10/10 sessions)
```

**Check for database write errors:**
```bash
mcp__Railway__get-logs logType="deploy" filter="@level:error" lines=50
```

**Should see NO errors like:**
- ❌ `Could not find the 'extracted_at' column`
- ❌ `Could not find the 'raw_meta_summary' column`
- ❌ `Could not find the 'deep_analysis' column`

### Task 5: Verify Database State via Supabase

**Query to check Wave 1 completion:**
```sql
SELECT
  id,
  session_date,
  topics IS NOT NULL as has_topics,
  summary IS NOT NULL as has_summary,
  technique IS NOT NULL as has_technique,
  topics_extracted_at
FROM therapy_sessions
WHERE patient_id = '[latest_patient_id]'
ORDER BY session_date DESC;
```

**Expected result:**
- All 10 sessions should have `has_topics = true`
- All 10 sessions should have `topics_extracted_at` timestamp
- Timestamps should be within ~60-90 seconds of demo creation

**Query to check Wave 2 completion:**
```sql
SELECT
  id,
  session_date,
  prose_analysis IS NOT NULL as has_prose,
  prose_analyzed_at
FROM therapy_sessions
WHERE patient_id = '[latest_patient_id]'
ORDER BY session_date DESC;
```

---

## Success Criteria

### Phase 4 Success (Frontend)
- ✅ Session cards display within 3-5 seconds of page load
- ✅ "Analyzing..." placeholders show for empty topics/summary/actions
- ✅ No hardcoded mock data - all from API
- ✅ Hard refresh detection working on all pages
- ✅ Code deployed to Railway without errors

### Phase 5 Success (Backend)
- ⏳ No database column mismatch errors in Railway logs
- ⏳ Wave 1 analysis completes successfully for all 10 sessions
- ⏳ Wave 2 analysis completes successfully (if implemented)
- ⏳ Demo initialization completes within 30-40 seconds
- ⏳ No timeout errors on fresh demo creation

### End-to-End Success
- ⏳ New patient creation takes 30-40 seconds total
- ⏳ Session cards visible within 3-5 seconds
- ⏳ "Analyzing..." placeholders visible initially
- ⏳ Polling detects Wave 1 completion
- ⏳ Cards update with real data after 60-90 seconds
- ⏳ All 10 sessions show complete Wave 1 data

---

## Database Schema Reference

**Correct Column Names (from migration 009):**

**Wave 1 Timestamps:**
- ✅ `topics_extracted_at TIMESTAMP`
- ✅ `mood_analyzed_at TIMESTAMP`
- ✅ `breakthrough_analyzed_at TIMESTAMP`
- ❌ NOT `extracted_at`

**Wave 1 Data Fields:**
- ✅ `topics JSONB`
- ✅ `action_items JSONB`
- ✅ `technique TEXT`
- ✅ `summary TEXT`
- ✅ `extraction_confidence DECIMAL(3,2)`
- ❌ NOT `raw_meta_summary`

**Wave 2 Data Fields:**
- ✅ `prose_analysis TEXT` (verify in later migration)
- ❌ NOT `deep_analysis`

**Mood Analysis Fields:**
- ✅ `mood_score DECIMAL(3,1)`
- ✅ `mood_confidence DECIMAL(3,2)`
- ✅ `mood_rationale TEXT`
- ✅ `mood_indicators JSONB`
- ✅ `emotional_tone TEXT`

---

## Known Issues & Workarounds

### Issue 1: SSE Subprocess Isolation (From Dec 30)
- **Status:** Known limitation, polling fallback working
- **Impact:** Real-time updates via SSE don't work
- **Workaround:** 5-second polling checks `/api/demo/status`
- **Long-term fix:** Database-backed event queue (Phase 2 from Dec 30)

### Issue 2: Railway Log Buffering (From Dec 30)
- **Status:** Fixed with `print(..., flush=True)`
- **Impact:** Logs now visible in real-time
- **Verification:** Railway logs show per-session progress

### Issue 3: Backend Overload (Current)
- **Status:** Active blocker
- **Impact:** Cannot test any fixes until resolved
- **Solution:** Restart Railway service after fixing Wave 2 column

---

## Prompt for Separate Window

Use this prompt to continue work in a fresh Claude Code session:

```
I need to continue Phase 5 of the TherapyBridge dashboard implementation.

**Context:**
- Phase 4 (frontend) is COMPLETE and deployed: Session cards show "Analyzing..." placeholders immediately
- Backend has 2 database column fixes deployed, 1 pending
- Backend currently BLOCKED by stuck Wave 2 process - demo init timing out after 120 seconds

**Comprehensive Plan:**
See `thoughts/shared/plans/2026-01-01-phase-5-backend-database-fixes.md`

**Current Status:**
See `.claude/CLAUDE.md` lines 111-117 for blocker details

**Your tasks:**
1. Fix Wave 2 `deep_analysis` → `prose_analysis` column mismatch in `backend/scripts/seed_wave2_analysis.py`
2. Restart Railway backend to kill stuck process
3. Test full flow: fresh demo → cards with placeholders → Wave 1 completes → data appears
4. Verify no database errors in Railway logs
5. Confirm all 10 sessions get Wave 1 data within 60-90 seconds

**Success criteria:**
- Demo init completes in 30-40 seconds (not timeout)
- Session cards load in 3-5 seconds with "Analyzing..." placeholders
- Polling detects Wave 1 completion and updates cards
- Railway logs show no column mismatch errors
- All database writes succeed

Start by reading the comprehensive plan, then proceed with Task 1 (fix Wave 2 column).
```

---

## Timeline & Commits

**Phase 4 Commits (✅ Complete):**
- `5a6cec8` - Phase 4: Show session cards immediately with "Analyzing..." placeholders
- `477f442` - Update CLAUDE.md with Phases 1-3 completion status
- `1bd28e8` - Fix hard refresh detection on /sessions page
- `77f415b` - Fix critical database column name mismatch in Wave 1 analysis
- `ad38586` - Remove raw_meta_summary field - column doesn't exist in database

**Phase 5 Commits (⏳ Pending):**
- Next: Fix Wave 2 `deep_analysis` → `prose_analysis` column mismatch
- Next: Update plan status after successful testing

---

## References

**Key Files:**
- Frontend hook: `frontend/app/patient/lib/usePatientSessions.ts`
- Session cards: `frontend/app/patient/components/SessionCard.tsx`
- Wave 1 script: `backend/scripts/seed_wave1_analysis.py`
- Wave 2 script: `backend/scripts/seed_wave2_analysis.py`
- Database schema: `backend/supabase/migrations/009_add_mood_and_topic_analysis_columns.sql`

**Documentation:**
- Master doc: `Project MDs/TherapyBridge.md`
- Session history: `.claude/SESSION_LOG.md`
- Phase 4 plan: `thoughts/shared/plans/2025-12-31-phase-4-session-cards-immediate-display.md`
- SSE fix doc: `Project MDs/CRITICAL_FIX_sse_and_logging.md`

**Related Sessions:**
- Dec 30: SSE subprocess isolation + Railway logging fixes
- Dec 31: Hard refresh detection + SSE connection timing
- Jan 1: Phase 4 implementation + database column fixes

---

**END OF PHASE 5 PLAN**
