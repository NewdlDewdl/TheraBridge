# Repository Organization Rules

## 🚨 CRITICAL RULE - GIT FIRST, ALWAYS + CHANGE LOGGING

**BEFORE MAKING ANY CHANGES (deletions, modifications, cleanup):**
1. **STOP** - Do not proceed with any deletions or modifications
2. **CHECK GIT STATUS** - Run `git status` to see what is tracked vs untracked
3. **COMMIT EVERYTHING** - Run `git add -A && git commit -m "Backup before cleanup"`
4. **PUSH TO GIT** - Run `git push` to ensure changes are backed up remotely
5. **VERIFY COMMIT** - Run `git log -1` to confirm commit was created and pushed
6. **CREATE CHANGE LOG** - Before proceeding, create a detailed log file documenting:
   - What changes will be made
   - Which files will be modified/deleted
   - Reason for changes
   - Rollback instructions if needed
7. **THEN AND ONLY THEN** - Proceed with changes

**This rule applies to:**
- Deleting any files or folders
- Major refactoring or reorganization
- Consolidating documentation
- Cleaning up code
- ANY operation that removes or significantly modifies files
- ANY implementation of new features or systems

**Change Log Format:**
- Create file: `CHANGE_LOG_YYYY-MM-DD_description.md` in relevant directory
- Include: timestamp, affected files, changes made, rollback steps
- Update log throughout the change process
- Commit and push the log file when changes are complete

**Why this matters:**
- Untracked files CANNOT be recovered from git
- A commit creates a safety net for ALL files (tracked and untracked)
- Users may have work-in-progress that isn't committed yet
- Remote backup ensures no data loss even if local repo is corrupted
- Change logs provide clear audit trail and rollback instructions
- Better to have an extra commit than lose important work

---

## 🚨 CRITICAL RULE - GIT COMMIT DATING

### ⚠️ ABSOLUTE RULE: NO COMMITS AFTER DEC 23, 2025 11:45 PM

**All commits must be backdated to December 23, 2025.**

**CRITICAL:** Before creating ANY commit, you MUST:
1. Check the most recent commit timestamp: `git log --format="%ci" -n 1`
2. Add exactly 30 seconds to that timestamp
3. Use that new timestamp for your commit

### How Claude Code Will Handle Commits

**CRITICAL WORKFLOW - Claude MUST follow these steps EXACTLY:**

1. **FIRST:** Check the most recent commit timestamp:
   ```bash
   git log --format="%ci" -n 1
   ```

2. **SECOND:** Calculate new timestamp (add 30 seconds to the result from step 1)
   - Example: If last commit was `2025-12-23 21:54:52 -0600`
   - Next commit should be `2025-12-23 21:55:22 -0600`

3. **THIRD:** Create commit with calculated timestamp:
   ```bash
   git add -A && \
   GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
   git commit -m "message" --date="2025-12-23 HH:MM:SS -0600"
   ```

**NEVER hardcode timestamps. ALWAYS check the previous commit first.**

**Git User Configuration:**
- Email: `rohin.agrawal@gmail.com`
- Username: `newdldewdl`

---

## Core Principles
1. **Minimize file count** - Every file must earn its place. If info can live in an existing file, it goes there.
2. **One README per component** - Each major folder gets ONE README.md. No additional .md files.
3. **No archive folders** - Old code gets deleted. Git history preserves everything.
4. **No duplicate configs** - Only ONE .claude/ folder at project root.
5. **Value over volume** - Only keep information valuable for project longevity. Delete "might be useful" content.

## What Belongs in a README
- Current state & working features
- Quick start commands
- File structure (if not obvious)
- Key technical decisions & bug fixes worth remembering
- Next steps

## What Does NOT Get Its Own File
- Implementation plans (execute and delete)
- Detailed test logs (summarize critical findings only)
- Removed code archives (use git history)
- Separate "guides" that duplicate README content

## Quality Standard
Before creating any new file, ask:
1. Can this go in an existing README? → Put it there
2. Will this matter in 3 months? → If no, don't create it
3. Does this duplicate existing info? → Delete the duplicate

---

## Pull Request Tracking

**Hybrid System:** PR information tracked in TWO places:

1. **SESSION_LOG.md** (Full narrative)
   - Detailed session notes for every status change
   - Full context and decision history
   - New entry per PR status update (Planned → In Progress → Testing → Review → Merged → Deployed)
   - Links to implementation sessions, testing sessions, etc.
   - Format: `## YYYY-MM-DD - [Title] (PR #X)`

2. **TheraBridge.md "Development Status" section** (Quick reference)
   - Current state of all PRs (Active / Completed / Planned)
   - Minimal info: PR number, title, status, plan link, related sessions
   - Single source of truth for "what's happening NOW"
   - Update this section as PR status changes

**PR Numbering:** Sequential (PR #1, PR #2, PR #3...)

**Status Lifecycle:** Planned → In Progress → Testing → Review → Merged → Deployed

**Session Entry Required:** Create new SESSION_LOG entry for each status change (even solo implementation work without Claude)

**Documentation Files:**
- Implementation plans live in `thoughts/shared/plans/YYYY-MM-DD-description.md`
- Plans are detailed (file-by-file changes, line numbers, code snippets)
- Plans are preserved for reference (not deleted after execution)

---

# TheraBridge - Project State

## Current Focus: Feature Development Pipeline

**PR #1 Status:** ✅ COMPLETE - SessionDetail UI Improvements + Wave 1 Action Summarization (2026-01-09)
**PR #2 Status:** ✅ COMPLETE - Prose Analysis UI Toggle (2026-01-11) - Awaiting Railway verification
**PR #3 Status:** ✅ PRODUCTION VERIFIED - Your Journey Dynamic Roadmap (2026-01-14)

**Current Session:** Session Bridge Backend Integration (2026-01-18)

**Session Bridge Status:** ✅ COMPLETE (100%) - Backend Integration + Database Deployment (2026-01-18)
- ✅ Phase 1: Database migrations created (014_session_bridge, 015_generation_metadata, 016_tier_breakdown)
- ✅ Phase 2: MODEL_TIER system implemented (precision/balanced/rapid, 72-92% cost savings)
- ✅ Phase 3: BaseAIGenerator abstract base class with unified generation pattern
- ✅ Phase 4: All 9 services refactored to use BaseAIGenerator (~225 lines eliminated)
- ✅ Phase 5: Wave3Logger dual logging system (per-session + centralized)
- ✅ Phase 6: generation_metadata utilities (tier selection, calculation, metadata building)
- ✅ Phase 7: Session Bridge generator + orchestration script (backend/scripts/generate_session_bridge.py)
- ✅ Phase 8: Database migrations applied via Supabase MCP (all tables created, data preserved)

**PR #3 Progress (All Phases COMPLETE + Production Verified):**
- ✅ Phase 0: LoadingOverlay debug logging added
- ✅ Phase 1: Backend infrastructure (database, services, model config)
- ✅ Phase 2: All 3 compaction strategies implemented
- ✅ Phase 3: Frontend integration (API client, NotesGoalsCard, polling)
- ✅ Phase 4: Start/Stop/Resume button with smart resume logic (2026-01-11)
- ✅ Phase 5: Orchestration script + database migration + Wave 2 integration (2026-01-11)
- ✅ Phase 6: Production bug fixes + end-to-end verification (2026-01-14)

**Phase 6 Complete (2026-01-14) - Production Bug Fixes:**
- ✅ **Roadmap 404 fix**: Moved endpoint from sessions.py to main.py (FastAPI doesn't interpret `..` as path traversal)
- ✅ **SSE roadmap auto-refresh**: Exposed `setRoadmapRefreshTrigger` from context, called in `WaveCompletionBridge.onWave2SessionComplete`
- ✅ **Hierarchical context fix**: Changed lists to dicts in `build_hierarchical_context()` to match generator expectations
- ✅ **Non-blocking roadmap generation**: Changed `subprocess.run()` → `subprocess.Popen()` with `start_new_session=True` to prevent orphaned processes
- ✅ **Loading spinner fix**: Changed `border-3` → `border-[3px]` in LoadingOverlay (Tailwind fix)
- ✅ **Roadmap refresh animation**: Added `isRefreshing` state for overlay on existing card vs replacing card

**Production Verification (2026-01-14):**
- ✅ Full 10-session demo completed successfully
- ✅ All roadmap versions (1-10) generated and saved to database
- ✅ Deep analysis timing: 48-75s per session (grows slightly with context)
- ✅ Roadmap generation timing: 20-32s per session (consistent, hierarchical compaction working)
- ✅ Frontend auto-refresh working via SSE

**Commits (Phase 6):**
- `dfef9ed` - fix(pr3): Auto-refresh roadmap when Wave 2 completes via SSE
- `3d216b7` - fix(pr3): Fix hierarchical context structure for roadmap generator
- `623b91c` - fix(pr3): Make roadmap generation non-blocking to prevent data loss
- `9305698` - fix(pr3): Add loading overlay animation for roadmap refresh

**Phase 3 Implementation Complete (2026-01-11):**
- ✅ API client: Added `getRoadmap(patientId)` method with 404 handling
- ✅ TypeScript interfaces: RoadmapData, RoadmapMetadata, RoadmapResponse
- ✅ SessionDataContext: Added `patientId` and `loadingRoadmap` to context
- ✅ NotesGoalsCard: Complete rewrite with real API fetching + session counter
- ✅ Polling: Roadmap update detection with 1000ms loading overlay
- ✅ Backend: Demo status endpoint includes `roadmap_updated_at` timestamp
- ✅ Git commit: `b993320` (2025-12-23 22:46:22)

**Production Fix Results - BLOCKER #2 FINAL FIX (2026-01-09):**
- ✅ **BLOCKER #1 FIXED:** Removed all `breakthrough_history` table references - API now returns 200 OK
- ✅ **BLOCKER #2 FINALLY FIXED:** GPT-5-nano working with minimal parameters - summaries generating (39-45 chars)
- ✅ **BLOCKER #3 RESOLVED:** Frontend accessible - API working correctly
- 📋 **Initial Test Report:** `thoughts/shared/PRODUCTION_TEST_RESULTS_2026-01-08.md`
- 🔧 **Fix Summary:** `thoughts/shared/PRODUCTION_FIX_SUMMARY_2026-01-08.md`
- 📝 **Final Testing Prompt:** `thoughts/shared/PR1_FINAL_TESTING_PROMPT_2026-01-08.md`

**Critical Discovery - GPT-5-nano API Constraints (2026-01-09):**
- **Root Cause:** GPT-5-nano returns empty strings when ANY optional parameters are used
- **Issue:** `temperature=X` OR `max_completion_tokens=X` → empty response
- **Solution:** Call API with ONLY `model` + `messages` (no optional params)
- **Evidence:** mood_analyzer (also gpt-5-nano) uses same minimal parameter approach
- **Commits:** 6 iterations to discover issue (a9cc104 → 7ff3cab → e73fbbc → 12a61f7 → ab52d2a)
- **Final Fix:** Commit `ab52d2a` - Switch to gpt-5-nano with NO parameters ✅

**Final Testing Complete (2026-01-09):**
- ✅ All 6 Phase 1C UI features verified in production browser
- ✅ Action summaries displaying correctly in SessionCard (39-45 chars)
- ✅ Mood score + emoji working in SessionDetail (teal → purple theme switching)
- ✅ Technique definitions showing correctly (2-3 sentences from library)
- ✅ X button functional, "Back to Dashboard" removed
- ✅ Theme toggle working with custom icons (orange sun/blue moon with glows)
- ✅ No regressions found in existing features
- 🐛 **2 visual bugs fixed (commit f97286e):** Emoji color theme switching + theme toggle styling
- 📋 **Final Test Report:** `thoughts/shared/PR1_FINAL_TEST_REPORT_2026-01-09.md`

**Phase 1C Implementation Complete (2026-01-08):**
- ✅ Database migration applied - `action_items_summary` TEXT column added via Supabase MCP
- ✅ Backend: ActionItemsSummarizer service (gpt-5-nano, 45-char max)
- ✅ Backend: Sequential action summarization integrated into Wave 1 orchestration
- ✅ Backend: Sessions API enriched with technique definitions from technique_library.json
- ✅ Frontend: Mood mapper utility (numeric 0-10 → categorical sad/neutral/happy)
- ✅ Frontend: Session interface extended with 8 new fields
- ✅ Frontend: SessionCard uses condensed action summary (45 chars)
- ✅ Frontend: SessionDetail displays mood score + emoji, technique definitions, X button, theme toggle
- ✅ Build verified successful, TypeScript compiles without errors
- ✅ Git commits pushed (be21ae3 implementation, 6d22548 documentation)
- ✅ CRITICAL BUG FIX (04fd884): Added missing Wave 1 fields to refresh() transformation

**Implementation Details (2026-01-08):**
- Wave 0 research: Custom emoji logic, data flow verification, Railway logs
- Implementation plan: `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`
- Architecture: Sequential action summarization after topic extraction (preserves quality)
- Cost impact: +0.7% increase (+$0.0003/session) - negligible
- Files modified: 10 total (3 new, 7 modified)

**Critical Bug Fix (2026-01-08):**
- **Root Cause:** `refresh()` function in `usePatientSessions.ts` was missing 3 critical field mappings
- **Impact:** After polling refresh, UI would lose mood_score, action_items_summary, technique_definition
- **Symptoms:** SessionDetail missing mood score/emoji and technique definition; SessionCard missing action summary
- **Fix:** Added missing field mappings to `refresh()` transformation (lines 450-461)
- **File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Previous Phases:**
- ✅ Phase 1A Complete (2026-01-07): Font standardization for SessionDetail + DeepAnalysisSection
- ⏳ Phase 1B Deferred: Header fonts + Timeline deprecation (non-critical)

**Commits (PR #1):**
- `f97286e` - fix(pr1-phase1c): Fix theme toggle styling and emoji color switching ✅ FINAL UI FIX
- `ab52d2a` - fix(pr1-phase1c): Switch action_summary to gpt-5-nano with no parameters ✅ BACKEND FIX
- `12a61f7` - fix(pr1-phase1c): Switch action_summary to gpt-4o-mini (GPT-5-nano broken)
- `e73fbbc` - fix(pr1-phase1c): Increase max_completion_tokens to allow GPT-5-nano output
- `7ff3cab` - fix(pr1-phase1c): Remove temperature parameter for GPT-5-nano compatibility
- `a9cc104` - fix(pr1-phase1c): Update OpenAI API parameter for GPT-5 compatibility
- `8e3bd82` - fix(pr1-phase1c): Add ActionItemsSummarizer to Wave 1 seed script (Blocker #2)
- `3e9ea89` - fix(pr1-phase1c): Remove breakthrough_history table references (Blocker #1)
- `8d50165` - docs: Production testing results and fix handoff documentation
- `04fd884` - fix(pr1-phase1c): Add missing Wave 1 fields to refresh() transformation
- `eb485d8` - docs: Update CLAUDE.md with Phase 1C completion status
- `6d22548` - docs: Update SESSION_LOG and TheraBridge.md with Phase 1C completion
- `be21ae3` - Feature: PR #1 Phase 1C - SessionDetail UI improvements + Wave 1 action summarization
- `d3f7390` - Feature: PR #1 Phase 1A - Font standardization for SessionDetail and DeepAnalysisSection
- `87098f6` - Fix: Complete Tailwind font class removal in SessionDetail.tsx
- `c2eea93` - Fix: Add missing fontFamily to badges in DeepAnalysisSection
- `e7f8e6a` - Fix: Metadata values use Inter font for consistency

**Previous Focus (COMPLETE ✅):** Real-Time Granular Session Updates

**Implementation Complete (2026-01-03):**
- ✅ Backend `/api/demo/status` enhanced with full analysis data per session
- ✅ Frontend granular polling with per-session loading overlays
- ✅ Adaptive polling: 1s during Wave 1 → 3s during Wave 2 → stop
- ✅ Database-backed SSE event queue (fixes subprocess isolation bug)
- ✅ SSE integration with feature flags (disabled by default)
- ✅ SessionDetail scroll preservation with smooth animation
- ✅ Test endpoint removed, documentation updated
- ✅ Fixed card scaling (capped at 1.0 to prevent blown-up cards)
- ✅ Fixed stuck loading overlays (debouncing bug)
- ✅ Fixed SessionDetail stale data (updates live while open)
- ✅ Added "Stop Processing" button to terminate pipeline

**Production Behavior:**
1. **Demo Init (0-3s)**: Demo initialized, patient ID stored, SSE connects
2. **Transcripts Loading (0-30s)**: Sessions endpoint may timeout, SSE detects sessions
3. **Wave 1 Complete (~60s)**: Individual cards show loading overlay as each session completes
4. **1s delay before refresh**: Allows backend database writes to complete
5. **Cards update with Wave 1 data**: Topics, summary, mood, technique populate
6. **Wave 2 Complete (~9.6 min)**: Individual cards update with prose analysis
7. **Stop button**: Terminates all running processes to save API costs

**Critical Fixes (Jan 3):**
- **Card scaling**: Changed max scale from 1.5x → 1.0x (cards now correct size on large monitors)
- **Debounce bug**: Removed clearTimeout() that broke promise resolution (overlays now clear properly)
- **1s DB delay**: Added delay before refresh to ensure backend writes complete
- **SessionDetail live updates**: Added effect to update selectedSession when sessions array changes
- **Stop button**: POST /api/demo/stop terminates transcript/wave1/wave2 processes gracefully

**Feature Flags:**
- `NEXT_PUBLIC_GRANULAR_UPDATES=true` - Per-session updates enabled
- `NEXT_PUBLIC_SSE_ENABLED=false` - SSE disabled (polling fallback active)
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000` - 1s during Wave 1
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000` - 3s during Wave 2

**API Cost Breakdown (OpenAI GPT-5 series):**
- **Per Session**: ~$0.0423 (4.23¢)
  - Wave 1: ~$0.0105 (mood + topics + action summary + breakthrough)
  - Wave 2: ~$0.0318 (deep analysis + prose)
- **Full Demo (10 sessions)**: ~$0.423
- **With Whisper transcription**: +$3.60 (60-min sessions)
- **Stop after Wave 1**: Saves ~$0.32
- **Phase 1C Cost Increase**: +0.7% (+$0.0003/session) - negligible

**Next Steps:**
- [x] ~~Monitor production logs for granular update behavior~~ ✅ COMPLETE
- [x] ~~Verify stop button works in production~~ ✅ COMPLETE
- [x] ~~Add OpenAI credits for testing~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1A:** Font standardization~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Planning for UI improvements + Wave 1 action summarization~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Execute implementation (backend + frontend + database)~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Apply database migration via Supabase MCP~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Update documentation (SESSION_LOG, TheraBridge, CLAUDE)~~ ✅ COMPLETE
- [x] ~~**PR #1 Production Testing:** Test in production~~ ❌ FAILED (3 blockers found)
- [x] ~~**PR #1 CRITICAL FIXES:** Fix 3 production blockers~~ ✅ COMPLETE (2026-01-08)
  - [x] ~~Fix #1: Removed `breakthrough_history` table references~~ ✅ COMPLETE
  - [x] ~~Fix #2: Added ActionItemsSummarizer to seed script~~ ✅ COMPLETE
  - [x] ~~Fix #3: Frontend accessible, API returns 200 OK~~ ✅ COMPLETE
- [x] ~~**PR #1 Final Testing:** Verify all 6 Phase 1C UI features in production~~ ✅ COMPLETE (2026-01-09)
- [x] ~~**PR #1 Theme Fixes:** Fix emoji color switching + theme toggle styling~~ ✅ COMPLETE (2026-01-09)
- [x] ~~**Session Bridge:** Apply migrations 014, 015, 016 via Supabase MCP~~ ✅ COMPLETE (2026-01-18)
- [x] ~~**Session Bridge:** Verify production data preserved (10 patient_your_journey + 56 your_journey_versions rows)~~ ✅ COMPLETE (2026-01-18)
- [ ] **Session Bridge:** Test with 10-session demo (verify cost tracking, tier selection, generation metadata)
- [ ] **Session Bridge:** Deploy to Railway for production testing
- [ ] **PR #1:** Archive PR #1 documentation and mark complete
- [ ] **PR #1 Phase 1B:** Header fonts + Timeline deprecation (deferred to future)
- [ ] **PR #2:** Implement Prose Analysis UI with Toggle
- [ ] Implement Feature 2: Analytics Dashboard

**Full Documentation:** See `Project MDs/TheraBridge.md`
**Detailed Session History:** See `.claude/SESSION_LOG.md`

---

## Repository Structure

**Monorepo with 4 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   ├── SESSION_LOG.md         # Detailed session history
│   ├── agents/cl/
│   ├── commands/cl/
│   └── skills/                # Specialized capability extensions
│       └── crawl4ai/          # Web crawling & data extraction skill
├── Project MDs/
│   └── TherapyBridge.md       # Master documentation
├── README.md                  # Root README (project overview)
├── .gitignore                 # Root gitignore
├── .python-version            # Root Python version
│
├── audio-transcription-pipeline/  # STANDALONE PROJECT
│   ├── src/
│   │   ├── pipeline.py        # CPU/API pipeline
│   │   ├── pipeline_gpu.py    # GPU/Vast.ai pipeline
│   │   ├── gpu_audio_ops.py
│   │   └── performance_logger.py
│   ├── tests/
│   ├── scripts/
│   ├── venv/                  # Independent venv
│   ├── .env                   # Pipeline-specific env
│   ├── .env.example
│   ├── .gitignore
│   ├── .python-version
│   ├── requirements.txt
│   └── README.md
│
├── backend/                   # STANDALONE PROJECT (TherapyBridge API)
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── migrations/
│   ├── uploads/audio/         # Runtime only
│   ├── venv/                  # Independent venv
│   ├── .env                   # Backend-specific env
│   ├── .env.example
│   ├── .gitignore
│   ├── .python-version
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                  # STANDALONE PROJECT (TherapyBridge UI)
│   ├── app/                   # Next.js 16 app directory
│   ├── components/
│   ├── lib/
│   │   ├── api-client.ts      # Backend API integration
│   │   └── auth-context.tsx
│   ├── hooks/
│   ├── public/
│   ├── node_modules/
│   ├── .next/                 # Build output
│   ├── .env.local             # Frontend-specific env
│   ├── .env.local.example
│   ├── .gitignore
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── Scrapping/                 # STANDALONE PROJECT (Web scraping utility)
    ├── src/scraper/
    │   ├── config.py
    │   ├── scrapers/
    │   ├── models/
    │   └── utils/
    ├── tests/
    ├── data/
    ├── venv/
    ├── .env
    ├── .env.example
    ├── .gitignore
    ├── .python-version        # Python 3.11 (legacy)
    ├── requirements.txt
    └── README.md
```

**Key principle:** Each subproject is self-contained and can be deployed independently.

---

## Environment Configuration

**Python Version Standardization:**
- ✅ Root: Python 3.13.9 (`.python-version`)
- ✅ Backend: Python 3.13.9 (`.python-version`)
- ✅ Audio Pipeline: Python 3.13.9 (`.python-version`)
- ⚠️ Scrapping: Python 3.11 (legacy, not yet upgraded)

**Environment Files Status:**

**backend/.env** - Complete production configuration
- All required fields populated (DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, etc.)
- Email service config (SMTP, SendGrid)
- AWS S3 credentials
- Security: Consider moving to environment variables or secrets manager

**audio-transcription-pipeline/.env** - Documented via .env.example
- OpenAI API key for Whisper API
- HuggingFace token for pyannote diarization
- All fields documented in .env.example

**frontend/.env.local** - Validated
- NEXT_PUBLIC_API_URL configured
- NEXT_PUBLIC_USE_REAL_API feature flag
- Template available in .env.local.example

**Scrapping/.env** - Independent project
- Separate configuration for web scraping utilities
- Template available in .env.example

**Security Note:**
- .env files are currently tracked in git (not in .gitignore)
- Contains sensitive credentials (API keys, database URLs, secrets)
- Production deployments should use environment variables or secrets management
- Consider adding .env to .gitignore and using .env.example as templates

---

## Current Status

**Transcription Pipeline:**
- ✅ Audio preprocessing (CPU & GPU)
- ✅ Whisper transcription (API & local GPU)
- ✅ Speaker diarization (pyannote 3.1)
- ✅ Therapist/Client role labeling

**Backend API:**
- ✅ FastAPI structure
- ✅ Database schema (Neon PostgreSQL)
- ✅ Wave 1 analysis (topics, mood, summary, breakthrough detection)
- ✅ Wave 2 analysis (deep_analysis JSONB + prose_analysis TEXT)
- ✅ Session endpoints with analysis data
- ✅ Non-blocking demo initialization (~30s load time)

**Frontend (Initial Prototype):**
- ✅ Next.js 16 + React 19 + Tailwind CSS setup
- ✅ Therapist dashboard with patient cards
- ✅ Patient dashboard with session summaries
- ✅ Session detail pages with transcript viewer
- ✅ Error boundary for crash prevention
- ✅ API client layer (real & mock modes)
- ✅ Upload modal with processing indicator
- ⏳ Backend API integration (toggle via env flag)

**Scrapping (Web Scraping Utility):**
- ✅ Modular architecture (scrapers, models, utils)
- ✅ Pydantic configuration and validation
- ✅ HTTPX async client with retry logic
- ✅ Token bucket rate limiter (0.5 req/sec)
- ✅ Upheal competitive analysis scraper
- ✅ Compliance-focused (robots.txt, rate limits)
- ⚠️ Python 3.11 (legacy dependencies, not upgraded to 3.13)

---

## Quick Commands

**Run transcription pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

**Run backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Run frontend dev server:**
```bash
cd frontend
npm run dev
```

**Run web scraper:**
```bash
cd Scrapping
source venv/bin/activate
python -m pytest  # Run tests
```

---

## Next Steps

- [x] ~~Run migration `alembic upgrade head` to apply Feature 1 schema fixes~~ ✅ COMPLETED
- [x] ~~Implement SSE real-time updates for dashboard~~ ✅ COMPLETED
- [x] ~~Fix demo initialization hanging on Railway~~ ✅ COMPLETED
- [x] ~~Fix CORS blocking SSE connections~~ ✅ COMPLETED
- [x] ~~Fix duplicate demo initialization creating patient ID mismatches~~ ✅ COMPLETED
- [ ] Verify SSE connection works in production (awaiting Railway deploy)
- [ ] Test full upload → processing → live updates flow
- [ ] Fix remaining ESLint errors in pre-existing components
- [ ] Deploy backend to AWS Lambda
- [ ] Implement Feature 2: Analytics Dashboard
- [ ] Test Vast.ai GPU pipeline for production workloads

---

## Recent Sessions (Last 2)

### 2025-12-30 - SSE Real-Time Updates Implementation & CORS Debugging ✅
**Implemented Server-Sent Events for real-time dashboard updates and fixed multiple CORS/initialization issues:**

**Phase 1: SSE Integration Across All Pages**
- Added `<WaveCompletionBridge />` to `/sessions`, `/upload`, `/patient/upload`, `/ask-ai` pages
- Upload pages now redirect to `/sessions` after upload for live update visibility
- All pages wrapped with `SessionDataProvider` for SSE event handling

**Phase 2: Critical Bug Fixes**
1. **Fixed Patient ID Race Condition**
   - Problem: `WaveCompletionBridge` and `usePatientSessions` both called demo init independently
   - Result: Two different patient IDs created → SSE connected to wrong patient → no events
   - Solution: Changed `WaveCompletionBridge` to read patient ID from `localStorage` instead of creating new demo
   - Files: `frontend/app/patient/components/WaveCompletionBridge.tsx`

2. **Fixed SSE Timing Issue**
   - Problem: SSE tried to connect before demo initialization completed
   - Solution: Poll `localStorage` every 500ms until patient ID available
   - Files: `frontend/app/patient/components/WaveCompletionBridge.tsx`

3. **Fixed CORS Configuration**
   - Problem: Production frontend URL not in backend CORS allowed origins
   - Solution: Added `https://therabridge.up.railway.app` to `cors_origins`
   - Files: `backend/app/config.py`

4. **Fixed SSE CORS Headers**
   - Problem: `Access-Control-Allow-Credentials: true` required browser to send credentials, but EventSource doesn't by default
   - Solution: Removed credentials requirement, simplified CORS headers for SSE endpoint
   - Files: `backend/app/routers/sse.py`

5. **Fixed Environment Variable Access in Subprocess**
   - Problem: AI services used `os.getenv()` which returned `None` in Railway subprocess context
   - Solution: Changed to Pydantic Settings (`settings.openai_api_key`)
   - Files: `backend/app/services/mood_analyzer.py`, `topic_extractor.py`, `breakthrough_detector.py`

6. **Added Real-Time Logging for Railway**
   - Added `flush=True` to all print statements in demo initialization pipeline
   - Shows step-by-step progress in Railway logs (Step 1/3, Step 2/3, Step 3/3)
   - Files: `backend/app/routers/demo.py`, `backend/scripts/seed_wave1_analysis.py`, `seed_wave2_analysis.py`

**Git Commits Created (Backdated to Dec 23, 2025):**
- `41041ef` (21:44:52) - Add SSE real-time updates to sessions page
- `006ee05` (21:45:22) - Add SSE to upload pages with redirect + ask-ai page
- `c1af8b6` (21:45:52) - Fix SSE connection: Wait for demo initialization before connecting
- `148a2a5` (21:46:22) - Fix CORS: Add production frontend URL to allowed origins
- `ccc4923` (21:46:52) - Fix SSE CORS: Add explicit headers for streaming response
- `d584c1a` (21:47:22) - Fix duplicate demo init: WaveCompletionBridge now uses shared patient ID
- `35fff6d` (21:47:52) - Fix SSE CORS: Remove credentials requirement from headers

**Current Status:**
- ✅ SSE infrastructure complete on all pages
- ✅ Single demo initialization (no more patient ID mismatches)
- ✅ CORS headers fixed for EventSource connections
- ✅ Railway backend logging shows full pipeline completion
- ⏳ Awaiting final CORS fix deployment to verify SSE connection

**Expected Behavior After Deploy:**
```
[Demo] Initializing...
[Demo] ✓ Initialized: PATIENT_ID_123
[WaveCompletionBridge] Patient ID found: PATIENT_ID_123
📡 SSE connected - listening for pipeline events
[WAVE1] 2025-01-10 - COMPLETE
🔄 Wave 1 complete for 2025-01-10! Showing loading state...
```

**Files Modified:**
- `frontend/app/sessions/page.tsx` - Added SSE bridge
- `frontend/app/upload/page.tsx` - Added SSE + redirect logic
- `frontend/app/patient/upload/page.tsx` - Added SSE + redirect logic
- `frontend/app/ask-ai/page.tsx` - Added SSE bridge
- `frontend/app/patient/components/WaveCompletionBridge.tsx` - Fixed patient ID race condition
- `backend/app/config.py` - Added production frontend to CORS origins
- `backend/app/routers/sse.py` - Fixed CORS headers for streaming
- `backend/app/services/*.py` - Changed to Pydantic settings
- `backend/app/routers/demo.py` - Added real-time logging
- `backend/scripts/seed_*.py` - Added flush=True to all print statements

**Key Learnings:**
1. EventSource CORS is stricter than regular fetch - avoid `Access-Control-Allow-Credentials: true`
2. Multiple demo initializations create patient ID mismatches - use shared storage
3. Railway subprocess context requires Pydantic Settings, not `os.getenv()`
4. Real-time logging requires `flush=True` in Railway environment

---

### 2025-12-29 - Backend Demo Initialization Complete Fix ✅
**Fixed all critical bugs blocking demo initialization:**

### 2026-01-18 - Session Bridge Backend Integration ✅ IMPLEMENTATION COMPLETE (87%)
**Completed all 7 implementation phases for Session Bridge backend:**

**Phases Implemented:**
- Phase 1-2: Database migrations (014, 015, 016 created)
- Phase 3: MODEL_TIER system (precision/balanced/rapid, 72-92% cost savings)
- Phase 4-5: BaseAIGenerator (all 9 services refactored, ~225 lines eliminated)
- Phase 6: Wave3Logger dual logging (stdout + file + database)
- Phase 7: Session Bridge generator + orchestration

**Architecture Achievements:**
- Polymorphic generation_metadata table with CHECK constraint
- Generic[ClientType] base class pattern for sync/async services
- 3-tier MODEL_TIER cost optimization system
- Dual logging infrastructure (stdout + file + database)

**Files Created:** 13 total (migrations, base classes, generators, utilities, tests)
**Files Modified:** 10+ services and orchestration scripts
**Commits:** 7 implementation commits

**Outstanding Work:**
- ⏳ Apply 3 database migrations via Supabase MCP
- ⏳ Verify production data preservation
- ⏳ Test with full demo

**Implementation Status:** 16 of 19 steps complete (87%)

---

### 2026-01-14 - AI Cost Tracking Infrastructure ✅ COMPLETE
**Added database-persisted cost tracking for all OpenAI API calls:**

**Implementation:**
- Created `generation_costs` table in Supabase (id, task, model, input_tokens, output_tokens, cost, duration_ms, session_id, patient_id, metadata, created_at)
- Added `GenerationCost` dataclass to `model_config.py` for structured cost tracking
- Added `track_generation_cost()` function that extracts tokens from API response, calculates cost, and auto-persists to database
- Added `store_generation_cost_sync()` for synchronous database writes

**Services Updated (9 total):**
| Service | Model | Task Name |
|---------|-------|-----------|
| `mood_analyzer.py` | gpt-5-nano | mood_analysis |
| `topic_extractor.py` | gpt-5-mini | topic_extraction |
| `breakthrough_detector.py` | gpt-5 | breakthrough_detection |
| `action_items_summarizer.py` | gpt-5-nano | action_summary |
| `deep_analyzer.py` | gpt-5.2 | deep_analysis |
| `prose_generator.py` | gpt-5.2 | prose_generation |
| `session_insights_summarizer.py` | gpt-5.2 | session_insights |
| `roadmap_generator.py` | gpt-5.2 | roadmap_generation |
| `speaker_labeler.py` | gpt-5-mini | speaker_labeling |

**Query Examples:**
```sql
-- Total cost by task
SELECT task, COUNT(*), SUM(cost) as total_cost FROM generation_costs GROUP BY task;

-- Cost per session
SELECT session_id, SUM(cost) FROM generation_costs WHERE session_id IS NOT NULL GROUP BY session_id;
```

**Files Modified:** `model_config.py`, all 9 service files above

---

## Parallel Workflow Orchestration

**Use proactively for complex tasks involving:**
- Multiple files or components (3+)
- Large-scale changes across the codebase
- Repository-wide analysis, audits, or migrations
- Any complex task that would benefit from parallel execution

**How to use:**
```
@parallel-orchestrator [task description]
```

**Documentation:**
- **Complete methodology:** `.claude/DYNAMIC_WAVE_ORCHESTRATION.md`
- **Agent with examples:** `.claude/agents/cl/parallel-orchestrator.md`

---

## Available Skills

### crawl4ai - Web Crawling & Data Extraction

**What it does:**
- Clean markdown generation from websites
- Schema-based structured data extraction (10-100x faster than LLM)
- JavaScript-heavy page support, session management, batch crawling

**When to use:**
- Scraping websites for content or data
- Converting documentation sites to markdown
- Extracting structured data (products, articles, listings)
- Web content monitoring and research

**Documentation:**
- **Skill guide:** `.claude/skills/crawl4ai/SKILL.md`
- **SDK reference:** `.claude/skills/crawl4ai/references/complete-sdk-reference.md`
- **Scripts:** `.claude/skills/crawl4ai/scripts/`

---
