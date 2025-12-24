# Continue Real-Time Granular Session Updates Implementation

## Context

You are continuing the implementation of the **Real-Time Granular Session Updates** feature for TheraBridge (formerly TherapyBridge). This is a 4-phase implementation to add per-session real-time updates with loading overlays, fix SSE subprocess isolation bug, and optimize polling.

**Current Progress:**
- ✅ **Phase 1 Complete**: Backend `/api/demo/status` enhanced with full analysis data per session
- ✅ **Phase 2 Partial Complete**: Frontend granular polling with change detection and adaptive intervals
- ⏳ **Phase 2 Remaining**: SessionDetail scroll preservation + backend test endpoint + verification
- ⏳ **Phase 3 Pending**: Database-backed SSE event queue
- ⏳ **Phase 4 Pending**: SSE integration + documentation + TheraBridge rename

**Last Commits:**
- `87ea06d` - Phase 1: Enhance /api/demo/status with full analysis data per session
- `b2f9802` - Phase 2 (Partial): Add polling config and refactor usePatientSessions
- `0d6d293` - Update documentation with Phase 1-2 progress

---

## Implementation Plan Reference

**CRITICAL**: Read the complete implementation plan before proceeding:
- **File**: `.claude/plans/2026-01-03-realtime-session-updates.md`
- This contains exact code snippets, success criteria, and detailed instructions for all phases

---

## What You Need to Do

### Phase 2: Complete Remaining Tasks

**Remaining Tasks from Plan:**

1. **SessionDetail Scroll Preservation** (Section 2.6-2.8)
   - File: `frontend/app/patient/components/SessionDetail.tsx`
   - Add refs: `leftColumnRef`, `rightColumnRef`, `previousSessionIdRef`
   - Add scroll preservation effect (lines after refs definition)
   - Add refs to scroll containers (lines 102, 140)
   - **Exact code in plan lines 579-662**

2. **Backend Test Endpoint** (Section 2.9)
   - File: `backend/app/routers/demo.py`
   - Add `POST /api/demo/test-complete-session/{session_id}` endpoint
   - Allows manual Wave 1/Wave 2 completion for testing
   - **IMPORTANT**: This is TESTING ONLY - will be removed in Phase 4
   - **Exact code in plan lines 663-736**

3. **Automated Verification** (Success Criteria section 2)
   - Frontend builds: `cd frontend && npm run build`
   - TypeScript check: `cd frontend && npm run type-check`
   - Linting: `cd frontend && npm run lint`
   - Verify environment variables load correctly
   - Verify polling starts/switches/stops correctly

4. **Manual Verification** (Success Criteria section 2)
   - Hard refresh → Demo init → Sessions load with 1s polling
   - Use test endpoint to complete Session #1 Wave 1 → Only card #1 shows loading overlay
   - Use test endpoint to complete Session #2 Wave 1 → Only card #2 shows loading overlay
   - Observe polling interval switch from 1s → 3s after Wave 1 complete
   - Open SessionDetail for Session #3 → Complete Session #5 Wave 1 → Detail page doesn't refresh
   - Scroll down in SessionDetail → Update that session → Scroll position preserved
   - Wave 2 completes → Polling stops

**After Phase 2 Verification:**
- Commit changes with proper git dating (check last commit timestamp, add 30 seconds)
- Push to Railway
- Get user confirmation before proceeding to Phase 3

---

### Phase 3: Database-Backed SSE Event Queue

**Overview:** Create `pipeline_events` table to replace in-memory `PipelineLogger._event_queue`. This fixes the subprocess isolation bug where events written in seed scripts never reach the FastAPI SSE endpoint.

**Tasks from Plan:**

1. **Create Database Migration** (Section 3.1-3.2)
   - File: `backend/supabase/migrations/013_add_pipeline_events_table.sql` (NEW)
   - Apply via Supabase MCP: `mcp__supabase__apply_migration`
   - **Exact SQL in plan lines 775-817**

2. **Add Environment Variable** (Section 3.3)
   - Files: `backend/.env.example`, `backend/.env`
   - Add: `PIPELINE_EVENT_RETRY_MODE=development`

3. **Refactor PipelineLogger** (Section 3.4)
   - File: `backend/app/services/pipeline_logger.py`
   - Modify `log_event()` method to write to database
   - Add retry logic (3 attempts in development mode)
   - Fall back to in-memory queue if database fails
   - **Exact code in plan lines 864-954**

4. **Update SSE Endpoint** (Section 3.5)
   - File: `backend/app/routers/sse.py`
   - Replace in-memory queue logic with database queries
   - Query unconsumed events, mark as consumed after sending
   - **Exact code in plan lines 956-1066**

5. **Verification** (Success Criteria section 3)
   - Automated: Migration applies, table exists, indices created, backend starts
   - Manual: Run seed script → Events in database → SSE sends events → Events marked consumed

**After Phase 3 Verification:**
- Commit changes with proper git dating
- Push to Railway
- Get user confirmation before proceeding to Phase 4

---

### Phase 4: SSE Integration + Documentation + TheraBridge Rename

**Overview:** Integrate SSE with granular polling, remove test endpoint, update all documentation, and rename project from TherapyBridge to TheraBridge.

**Tasks from Plan:**

1. **Update WaveCompletionBridge** (Section 4.1)
   - File: `frontend/app/patient/components/WaveCompletionBridge.tsx`
   - Implement no-stagger SSE updates (instant loading overlays)
   - Respect `NEXT_PUBLIC_SSE_ENABLED` feature flag
   - **Exact code in plan lines 1100-1156**

2. **Update Polling for SSE Priority** (Section 4.2)
   - File: `frontend/app/patient/lib/usePatientSessions.ts`
   - Disable polling when SSE enabled
   - **Exact code in plan lines 1159-1189**

3. **Remove Test Endpoint** (Section 4.3)
   - File: `backend/app/routers/demo.py`
   - Delete `/test-complete-session/{session_id}` endpoint

4. **Update Environment Variables** (Section 4.4)
   - File: `frontend/.env.local`
   - Set production defaults (SSE disabled, debug logging off)

5. **Update Documentation** (Section 4.5-4.7)
   - **CLAUDE.md**: Update Current Focus section with completion status
   - **SESSION_LOG.md**: Mark as complete with commit hashes
   - **Rename**: `Project MDs/TherapyBridge.md` → `Project MDs/TheraBridge.md`
   - **Find/Replace**: All references `TherapyBridge` → `TheraBridge`
   - **Exact updates in plan lines 1228-1335**

6. **Comprehensive Verification** (Success Criteria section 4)
   - Test granular polling (SSE disabled)
   - Test SSE real-time (SSE enabled)
   - Test feature flag rollback
   - Verify all documentation updated

**After Phase 4 Complete:**
- Final commit with proper git dating
- Push to Railway
- Declare implementation complete!

---

## Important Reminders

### Git Commit Dating Rules
**CRITICAL**: All commits must be backdated to December 23, 2025.

**Workflow:**
1. Check last commit timestamp: `git log --format="%ci" -n 1`
2. Add exactly 30 seconds to that timestamp
3. Use that new timestamp for your commit:
   ```bash
   git add -A && \
   GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
   git commit -m "message" --date="2025-12-23 HH:MM:SS -0600"
   ```

**Git User Configuration:**
- Email: `rohin.agrawal@gmail.com`
- Username: `newdldewdl`

### Railway Deployment
- User is testing on Railway only (no local testing)
- Always push changes and wait ~30 seconds for deployment
- Use Railway MCP tools to check logs: `mcp__Railway__get-logs`

### Supabase MCP
- Use `mcp__supabase__apply_migration` for database migrations
- Use `mcp__supabase__execute_sql` for testing queries

### Implementation Plan is Your Guide
- **Every code change is documented in the plan with exact line numbers and code snippets**
- **Follow the plan exactly - don't improvise**
- **Use the success criteria to verify each phase**

---

## File Locations Quick Reference

**Implementation Plan:**
- `.claude/plans/2026-01-03-realtime-session-updates.md`

**Documentation:**
- `.claude/CLAUDE.md` - Project state
- `.claude/SESSION_LOG.md` - Session history
- `Project MDs/TherapyBridge.md` - Main documentation (rename to TheraBridge in Phase 4)

**Backend Files:**
- `backend/app/routers/demo.py` - Demo status endpoint + test endpoint
- `backend/app/services/pipeline_logger.py` - Event logging (Phase 3)
- `backend/app/routers/sse.py` - SSE endpoint (Phase 3)
- `backend/supabase/migrations/` - Database migrations (Phase 3)

**Frontend Files:**
- `frontend/lib/polling-config.ts` - Polling configuration
- `frontend/app/patient/lib/usePatientSessions.ts` - Polling hook
- `frontend/app/patient/components/SessionDetail.tsx` - Scroll preservation (Phase 2)
- `frontend/app/patient/components/WaveCompletionBridge.tsx` - SSE updates (Phase 4)
- `frontend/.env.local` - Environment variables

---

## Start Here

**Your first task is to complete Phase 2:**

1. Read the implementation plan section 2.6-2.9 for SessionDetail scroll preservation + test endpoint
2. Implement the changes exactly as specified
3. Run automated verification (build, type-check, lint)
4. Commit with proper git dating
5. Push to Railway
6. Ask user to test manually using the test endpoint
7. Get confirmation before proceeding to Phase 3

**Good luck! The implementation plan has everything you need. Follow it closely and verify at each step.** 🚀
