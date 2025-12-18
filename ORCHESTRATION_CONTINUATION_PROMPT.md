# TherapyBridge MVP Completion - Orchestration Continuation Prompt

**Date Created:** 2025-12-18
**Status:** Ready for execution in fresh context window
**Backup Commit:** `fdf6784` - All research completed, plan validated

---

## 🎯 MISSION

Execute a corrected, research-based parallel orchestration to complete TherapyBridge MVP with 7 specialized orchestrators addressing validated gaps only.

---

## 📊 CONTEXT: What Happened Previously

### Wave 0 Research Completed ✅

Launched 5 parallel research agents that performed deep codebase analysis:

1. **Agent R1 (Explore):** Mapped complete monorepo structure
   - 4 independent projects: backend, frontend, audio-transcription-pipeline, scrapping
   - Backend: 80+ source files, 21 routers, 20 services, 50+ tests, 16 migrations
   - Frontend: 70+ files, 55 components, 16 hooks, 21 utilities, 10 pages
   - Created documentation: `COMPLETE_CODEBASE_MAP.txt`, `CODEBASE_QUICK_REFERENCE.txt`, `CODEBASE_EXPLORATION_INDEX.md`

2. **Agent R2 (Backend patterns):** Analyzed implementation patterns
   - FastAPI with async SQLAlchemy, layered architecture
   - JWT + TOTP MFA authentication with token rotation
   - Background processing via FastAPI BackgroundTasks
   - WeasyPrint for PDF, python-docx for DOCX exports

3. **Agent R3 (Frontend architecture):** Analyzed frontend patterns
   - Next.js 16 + React 19 + TypeScript
   - Discriminated union-based API client with auto token refresh
   - Intelligent polling with SWR (5s while processing, stops when complete)
   - Optimistic UI updates with automatic rollback

4. **Agent R4 (Feature file locations):** Located all feature-related files
   - Confirmed Feature 7 placeholder at `backend/app/routers/sessions.py:1154-1181`
   - Confirmed Feature 1 MFA validation fully implemented at `backend/app/routers/mfa.py:376-479`
   - Identified 7 failing tests (25/32 passing in security suite)

5. **Agent R5 (Test infrastructure):** Analyzed test patterns
   - pytest with 37.64% coverage (target: 80%)
   - 1834-line `conftest.py` with comprehensive fixtures
   - SQLite test database with WAL mode
   - MockAsyncOpenAI for AI service testing

### Git Backup Created ✅

```bash
Commit: fdf6784
Message: "Backup before orchestration: Complete TherapyBridge MVP with 7 parallel feature orchestrators"
Files: 5 changed, 2941 insertions(+), 2 deletions(-)
```

### Original Prompt Analysis Completed ✅

**Key Finding:** Original orchestration prompt contained **inaccurate assumptions** about codebase state:
- Claimed MFA validation "returns 501" → **INCORRECT** (fully implemented)
- Claimed export is placeholder → **CORRECT** (validated)
- Claimed 7 test failures → **CORRECT** (validated with root cause analysis)

### Corrected Plan Created ✅

Validated 7 TRUE gaps requiring work (see detailed plan below).

---

## ✅ VALIDATED GAPS (Real Work Required)

### Gap 1: Export Background Worker Implementation ⚠️ HIGH PRIORITY
**File:** `backend/app/routers/sessions.py:1154-1181`
**Status:** Placeholder with TODO comment
**Evidence:**
```python
async def process_timeline_export(...):
    """
    This is a placeholder that will be implemented by Backend Dev #3 (I7).
    """
    # TODO: Backend Dev #3 (I7) will implement this
    pass
```

**Work Required:**
- Implement actual PDF/DOCX/JSON generation
- Integrate with `backend/app/services/pdf_generator.py` and `docx_generator.py`
- Update ExportJob status: pending → processing → completed/failed
- Store file path in `ExportJob.file_path`
- Add file cleanup after 7 days (use `expires_at`)
- Write integration tests

**Files to Modify:**
- `backend/app/routers/sessions.py` (lines 1154-1181)
- `backend/app/tasks/export_worker.py` (NEW - create background worker)
- `backend/tests/routers/test_export_integration.py` (NEW)

**Success Criteria:**
- Background worker processes export jobs
- Files generated at `backend/exports/output/`
- Job status updates correctly
- Audit log records export event
- Files auto-delete after 7 days

---

### Gap 2: MFA Login Flow Integration ⚠️ HIGH PRIORITY
**Files:** `backend/app/auth/router.py:27-87` (login endpoint)
**Status:** MFA validation exists but NOT integrated into login flow

**Current Login Flow (lines 27-87):**
```python
@router.post("/login")
def login(credentials: UserLogin, db: Session):
    # Verify email/password
    # Generate tokens immediately (NO MFA check)
    return TokenResponse(access_token, refresh_token)
```

**Existing MFA Validation (ALREADY IMPLEMENTED at mfa.py:376-479):**
- Fully functional TOTP validation
- Backup code support
- Rate limiting (20/min)
- Session token verification

**Work Required:**
- Modify `/auth/login` to check `user.mfa_enabled` (add lines after password verification)
- If MFA enabled: return `{requires_mfa: true, session_token: "temp_token"}`
- If MFA disabled: return normal tokens
- Create `MFALoginResponse` schema in `backend/app/auth/schemas.py`
- Update router documentation
- Write integration tests for two-step flow

**NOT Required:**
- ❌ Implement `/mfa/validate` endpoint (ALREADY EXISTS)
- ❌ Implement TOTP service (ALREADY EXISTS)
- ❌ Create backup codes (ALREADY EXISTS)

**Success Criteria:**
- Users with MFA enabled must provide TOTP code during login
- Two-step login: email/password → TOTP validation → tokens
- Backup codes work as fallback
- Integration tests pass

---

### Gap 3: Frontend Integration Test Suite ⚠️ HIGH PRIORITY
**Status:** API client exists, hooks exist, but no E2E tests
**Dependencies:** Orchestrator 2 (MFA login flow)

**Work Required:**
- Create `frontend/tests/integration/` directory
- Test authentication flow:
  - Signup → Login → Token storage → Auto-refresh
  - Protected routes redirect correctly
  - Role-based access (therapist vs patient)
  - Logout clears tokens
  - **MFA login flow** (after Orchestrator 2 completes)
- Test session management:
  - Upload audio → Monitor processing (polling)
  - View session detail with extracted notes
  - View transcript with speaker labels
  - Create manual note using template
- Test patient management (create, view, stats)
- Test template system (list, create, use)
- Test error handling (401, network, validation, 500 errors)
- Performance testing (page load times, re-renders, caching)

**Success Criteria:**
- All user flows work end-to-end with real backend
- No console errors or warnings
- Token refresh works automatically
- Auto-polling stops appropriately
- Error states display correctly
- Performance acceptable (< 2s page loads)

---

### Gap 4: Frontend Analytics Dashboard 🔵 MEDIUM PRIORITY
**Status:** Backend complete, frontend doesn't exist
**Dependencies:** Orchestrator 3 (core integration testing)

**Backend Endpoints (READY):**
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/patients/{id}/progress`
- `GET /api/v1/analytics/sessions/trends`
- `GET /api/v1/analytics/topics`

**Work Required:**
- Install recharts: `npm install recharts`
- Create pages:
  - `frontend/app/therapist/analytics/page.tsx` (main dashboard)
  - `frontend/app/therapist/analytics/patient-progress/page.tsx`
  - `frontend/app/therapist/analytics/session-trends/page.tsx`
  - `frontend/app/therapist/analytics/topics/page.tsx`
- Create hooks:
  - `frontend/hooks/useAnalyticsOverview.ts`
  - `frontend/hooks/usePatientProgress.ts`
  - `frontend/hooks/useSessionTrends.ts`
  - `frontend/hooks/useTopicAnalytics.ts`
- Create chart components:
  - `frontend/components/analytics/OverviewStatsCards.tsx`
  - `frontend/components/analytics/SessionTrendsChart.tsx`
  - `frontend/components/analytics/TopicFrequencyChart.tsx`
  - `frontend/components/analytics/PatientProgressCard.tsx`
- Add time range filters (week, month, quarter, year)
- Add CSV export functionality

**Success Criteria:**
- Analytics dashboard displays real data from backend
- Charts render correctly with responsive design
- Time range filters update data correctly
- No performance issues with large datasets
- Mobile-friendly layout

---

### Gap 5: Frontend Patient Portal Real API Connection 🔵 MEDIUM PRIORITY
**Status:** Basic UI exists with mock data at `frontend/app/patient/page.tsx`
**Dependencies:** Orchestrator 3 (core integration testing)

**Current State:**
```typescript
// frontend/app/patient/page.tsx uses hardcoded data
const sessions = [
  { id: 1, date: "2024-01-15", summary: "Discussed anxiety..." },
  // ... mock data
];
```

**Backend Endpoints (READY):**
- `GET /api/patients/me` (get current patient)
- `GET /api/sessions/?patient_id={current_user_id}`
- `GET /api/v1/goals/?patient_id={current_user_id}`
- `GET /api/v1/goals/{id}/progress`

**Work Required:**
- Create hooks:
  - `frontend/hooks/useCurrentPatient.ts`
  - `frontend/hooks/usePatientSessions.ts`
  - `frontend/hooks/usePatientGoals.ts`
  - `frontend/hooks/useGoalProgress.ts`
- Update `frontend/app/patient/page.tsx` to use real data
- Create pages:
  - `frontend/app/patient/sessions/page.tsx` (session history)
  - `frontend/app/patient/goals/page.tsx` (goal tracking)
  - `frontend/app/patient/progress/page.tsx` (progress visualization)
- Create components:
  - `frontend/components/patient/SessionSummaryCard.tsx`
  - `frontend/components/patient/GoalProgressCard.tsx`
  - `frontend/components/patient/ActionItemList.tsx`
- **Security verification:**
  - Patients only see `patient_summary` (NOT `therapist_notes`)
  - Patients can only access their own data
  - Test with multiple patient accounts

**Success Criteria:**
- Patient portal displays real data from backend
- Patients only see patient_summary (not therapist_notes)
- Patients can only access their own sessions/goals
- Action item tracking works
- Goal progress displays correctly
- No security leaks (verified with test accounts)

---

### Gap 6: Email Verification System 🔵 MEDIUM PRIORITY
**Status:** Database field exists (`User.is_verified`), no service layer
**Dependencies:** None (independent)

**Current State:**
```python
# backend/app/models/db_models.py
class User(Base):
    is_verified = Column(Boolean, default=False, nullable=False)
    # No verification token system exists
```

**Work Required:**

**Backend:**
1. Choose email provider: SendGrid, AWS SES, or SMTP
2. Create `backend/app/services/email_service.py`:
   - `send_email(to, subject, body_html)` method
   - Template rendering support
3. Create verification token system:
   - Generate secure tokens (JWT or UUID + hash)
   - Store in database: `EmailVerification` table (user_id, token, expires_at)
   - Tokens expire after 24 hours
4. Add endpoints:
   - `POST /api/v1/auth/verify-email` (verify token)
   - `POST /api/v1/auth/resend-verification` (resend email)
   - `GET /api/v1/auth/verify-status` (check if verified)
5. Update signup flow (`backend/app/auth/router.py`):
   - After user registration, generate verification token
   - Send email with link: `http://frontend/auth/verify?token={token}`
   - User account remains `is_verified=false` until verified
6. Create email templates:
   - `backend/app/templates/emails/verification.html`
   - `backend/app/templates/emails/verification_success.html`
7. Add configuration:
   - `REQUIRE_EMAIL_VERIFICATION` env var (default: true in production)
   - `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM` env vars

**Frontend:**
1. Create `frontend/app/auth/verify/page.tsx`:
   - Read `token` from URL query params
   - Call `/api/v1/auth/verify-email` endpoint
   - Show success/error messages
   - Redirect to login after verification

**Files to Create:**
- `backend/app/services/email_service.py`
- `backend/app/routers/email_verification.py`
- `backend/app/models/email_verification.py`
- `backend/alembic/versions/xxx_add_email_verification.py` (migration)
- `backend/app/templates/emails/verification.html`
- `frontend/app/auth/verify/page.tsx`

**Files to Modify:**
- `backend/app/auth/router.py` (send email on signup)
- `backend/requirements.txt` (add email library)
- `backend/.env.example` (add email config)

**Success Criteria:**
- Signup sends verification email
- Verification link validates token and marks user as verified
- Expired tokens rejected (24h expiration)
- Resend verification works
- Email templates look professional
- Frontend verification page works
- Can toggle requirement via env var

---

### Gap 7: Fix Test Suite Authentication Infrastructure 🔵 MEDIUM PRIORITY
**Status:** 25/32 passing, 7 failing
**Dependencies:** None (may coordinate with Orchestrator 2)

**Failing Tests (from FEATURE_8_TEST_REPORT.md):**

1. **`test_security_headers_on_500_errors`** (middleware)
   - Error: Unhandled exception bubbling up
   - Fix: Add exception handler to test endpoint

2. **`test_complete_mfa_enrollment_flow`** (E2E)
   - Error: `assert 401 == 200` (Unauthorized)
   - Root cause: Authentication token not passed to endpoint

3. **`test_session_management_flow`** (E2E)
   - Error: `assert 401 == 200` (Unauthorized)
   - Root cause: Session endpoints require auth

4. **`test_audit_trail_created`** (E2E)
   - Error: `assert 401 == 200` (Unauthorized)
   - Root cause: Auth issue preventing audit log access

5. **`test_consent_workflow`** (E2E)
   - Error: `DetachedInstanceError` - User object not bound to session
   - Root cause: Session management issue (object accessed after session close)

6. **`test_emergency_access_workflow`** (E2E)
   - Error: `ObjectDeletedError` - User instance deleted
   - Root cause: CASCADE delete or transaction rollback

7. **`test_complete_security_integration`** (E2E)
   - Error: `OperationalError: no such table: users`
   - Root cause: Test database not initialized

**Work Required:**

1. **Fix Authentication (6 tests):**
   - Create `authenticated_client` fixture in `backend/tests/conftest.py`:
     ```python
     @pytest.fixture
     def authenticated_client(client, test_therapist_security):
         # Login and get token
         response = client.post("/api/v1/auth/login", json={
             "email": test_therapist_security.email,
             "password": "SecurePass123!@"
         })
         token = response.json()["access_token"]
         client.headers["Authorization"] = f"Bearer {token}"
         return client
     ```
   - Update E2E tests to use `authenticated_client` instead of `client`

2. **Fix Database Session Management (2 tests):**
   - Add `expire_on_commit=False` to test session configuration:
     ```python
     SessionLocal = sessionmaker(
         bind=engine,
         expire_on_commit=False  # Prevent detached instances
     )
     ```
   - Use `session.refresh(user)` before accessing relationships

3. **Fix Test Database Initialization (1 test):**
   - Ensure `Base.metadata.create_all(bind=engine)` called in test setup
   - Verify all models imported before creating tables

4. **Fix 500 Error Handler (1 test):**
   - Add exception handler to test app fixture
   - Verify headers present on 500 responses

**Files to Modify:**
- `backend/tests/conftest.py` (add authenticated_client fixture, fix session config)
- `backend/tests/e2e/test_security_flow.py` (use authenticated_client)
- `backend/tests/middleware/test_security_headers.py` (add exception handler)

**Success Criteria:**
- All 32 security tests passing (100%)
- No regressions in other test suites
- Tests properly isolated (can run in any order)
- Test execution time reasonable (< 2 minutes)
- `FEATURE_8_TEST_REPORT.md` updated with 32/32 passing

---

## 🌊 ORCHESTRATION STRUCTURE

### Wave 1: Independent Features (4 orchestrators in parallel)
**Duration:** 90-120 minutes

Launch simultaneously:
- **Orchestrator 1:** Export Background Worker Implementation
- **Orchestrator 2:** MFA Login Flow Integration
- **Orchestrator 6:** Email Verification System
- **Orchestrator 7:** Fix Test Suite Authentication

**Dependencies:** None - all independent

---

### Wave 2: Frontend Integration Testing (1 orchestrator)
**Duration:** 120 minutes

Launch when ready:
- **Orchestrator 3:** Frontend Integration Testing

**Dependencies:**
- **WAIT for Orchestrator 2** (MFA login flow) to complete before testing MFA flow
- Can start auth/session/patient tests immediately

---

### Wave 3: Frontend Feature Development (2 orchestrators in parallel)
**Duration:** 120 minutes

Launch simultaneously:
- **Orchestrator 4:** Analytics Dashboard
- **Orchestrator 5:** Patient Portal Real API Connection

**Dependencies:**
- **WAIT for Orchestrator 3** (core integration testing) to complete

---

## 📋 ORCHESTRATOR TASK PROMPTS

### Orchestrator 1: Export Background Worker Implementation

```
Implement the export background processing worker for Feature 7.

**Context from Research:**
- Placeholder confirmed at backend/app/routers/sessions.py:1154-1181
- Services exist: pdf_generator.py, docx_generator.py, report_generator.py
- Database models complete: ExportJob, ExportAuditLog, ExportTemplate

**Your Mission:**

1. Read the placeholder function at backend/app/routers/sessions.py:1154-1181
2. Analyze existing services:
   - backend/app/services/pdf_generator.py (WeasyPrint)
   - backend/app/services/docx_generator.py (python-docx)
   - backend/app/services/report_generator.py
3. Implement actual background processing:
   - Fetch timeline data for patient using database query
   - Generate PDF using pdf_generator.py service
   - Generate DOCX using docx_generator.py service
   - Generate JSON export (serialize timeline data)
   - Update ExportJob status: pending → processing → completed/failed
   - Store file path in ExportJob.file_path
   - Log to ExportAuditLog
4. Add file cleanup scheduler (7-day expiration via ExportJob.expires_at)
5. Write integration tests in backend/tests/routers/test_export_integration.py

**Files to Modify:**
- backend/app/routers/sessions.py (lines 1154-1181)
- backend/app/tasks/export_worker.py (NEW - create background worker)
- backend/tests/routers/test_export_integration.py (NEW)

**Success Criteria:**
- GET /api/v1/patients/{id}/timeline/export returns job ID
- Background worker processes job and generates files
- Job status updates: pending → processing → completed
- Files accessible via file_path
- Audit log records export event
- Files auto-delete after 7 days

**Report Format:**
When complete, provide:
- Implementation summary
- Test results (all tests passing)
- Sample export file paths
- Performance metrics (time to generate PDF/DOCX)
```

---

### Orchestrator 2: MFA Login Flow Integration

```
Integrate MFA validation into the login flow for Feature 1.

**Context from Research:**
- MFA validation endpoint FULLY IMPLEMENTED at backend/app/routers/mfa.py:376-479
- Login endpoint does NOT check MFA status at backend/app/auth/router.py:27-87
- TOTP service exists and works
- Backup codes exist and work

**Your Mission:**

1. Read current login flow at backend/app/auth/router.py:27-87
2. Read existing MFA validation at backend/app/routers/mfa.py:376-479 to understand how it works
3. Modify login flow (backend/app/auth/router.py):
   - After email/password validation (line 57), check if user.mfa_enabled
   - If MFA enabled:
     - Generate temporary session token
     - Return {requires_mfa: true, session_token: "temp_token"}
   - If MFA disabled:
     - Return normal JWT tokens (current behavior)
4. Create MFALoginResponse schema in backend/app/auth/schemas.py
5. Update login endpoint documentation
6. Write integration tests for two-step login flow:
   - Test 1: User with MFA disabled → receives tokens immediately
   - Test 2: User with MFA enabled → receives session_token, then validates with /mfa/validate
   - Test 3: Backup codes work during login

**DO NOT:**
- ❌ Modify /mfa/validate endpoint (already works perfectly)
- ❌ Modify TOTP service (already exists)
- ❌ Create backup code system (already exists)

**Files to Modify:**
- backend/app/auth/router.py (modify login function, lines 27-87)
- backend/app/auth/schemas.py (add MFALoginResponse)
- backend/tests/security/test_mfa_login_flow.py (NEW)

**Success Criteria:**
- Users with MFA enabled must provide TOTP code during login
- Two-step login flow works: email/password → session_token → TOTP validation → JWT tokens
- Backup codes work as fallback
- Integration tests pass

**Communication:**
- When complete, notify Orchestrator 3 (Frontend Testing) that MFA login flow is ready
- Provide example API calls with MFA enabled

**Report Format:**
When complete, provide:
- Implementation summary
- Updated login flow diagram
- Example API calls with MFA enabled
- Test results (all integration tests passing)
```

---

### Orchestrator 3: Frontend Integration Testing Specialist

```
Perform comprehensive end-to-end integration testing of frontend with live backend API.

**Context from Research:**
- Frontend uses real API via lib/api-client.ts
- Environment: NEXT_PUBLIC_API_URL=http://localhost:8000
- Hooks exist: useSession, useSessions, usePatients, useTemplates
- Auto-polling implemented (5s while processing, stops when complete)

**Your Mission:**

1. **Environment Setup:**
   - Verify .env.local has NEXT_PUBLIC_API_URL=http://localhost:8000
   - Start backend: cd backend && uvicorn app.main:app --reload
   - Start frontend: cd frontend && npm run dev

2. **Test Authentication Flow:**
   - Signup → Login → Token storage → Auto-refresh
   - Protected routes redirect correctly
   - Role-based access (therapist vs patient)
   - Logout clears tokens
   - **WAIT for Orchestrator 2** to complete MFA integration, then test MFA login flow

3. **Test Session Management:**
   - Upload audio file → Monitor processing status (auto-polling)
   - View session detail with extracted notes
   - View transcript with speaker labels
   - Create manual session note using template
   - Test all session filters and search

4. **Test Patient Management:**
   - Create patient → View patient detail
   - View patient sessions
   - Patient stats aggregation

5. **Test Template System:**
   - List templates (system + custom)
   - Create custom template
   - Use template for note writing
   - Test autofill from extracted notes

6. **Test Error Handling:**
   - Network errors → Retry logic
   - 401 errors → Token refresh → Retry
   - Validation errors → Form error display
   - 500 errors → Error boundary catches

7. **Performance Testing:**
   - Measure page load times
   - Check for unnecessary re-renders
   - Verify SWR caching works
   - Test auto-polling stops when session complete

**Communication Protocol:**
- Wait for Orchestrator 2 to notify when MFA login is ready
- Notify Orchestrator 4 (Analytics) and Orchestrator 5 (Patient Portal) when core integration testing complete
- Share any API contract issues discovered

**Success Criteria:**
- All user flows work end-to-end with real backend
- No console errors or warnings
- Token refresh works automatically
- Auto-polling stops appropriately
- Error states display correctly
- Performance acceptable (< 2s page loads)

**Report Format:**
When complete, provide:
- Test results for each flow (pass/fail)
- Screenshots of working features
- Performance metrics
- Any bugs or API contract mismatches discovered
- Recommendations for fixes
```

---

### Orchestrator 4: Analytics Dashboard Specialist

```
Implement the frontend analytics dashboard to visualize Feature 2 data.

**Context from Research:**
- Backend analytics endpoints complete:
  - GET /api/v1/analytics/overview
  - GET /api/v1/analytics/patients/{id}/progress
  - GET /api/v1/analytics/sessions/trends
  - GET /api/v1/analytics/topics
- Frontend has no analytics pages yet
- Need charts and visualizations

**Your Mission:**

1. **WAIT for Orchestrator 3** to complete core integration testing

2. **Install Chart Library:**
   - cd frontend && npm install recharts

3. **Create Analytics Pages:**
   - frontend/app/therapist/analytics/page.tsx (main dashboard)
   - frontend/app/therapist/analytics/patient-progress/page.tsx
   - frontend/app/therapist/analytics/session-trends/page.tsx
   - frontend/app/therapist/analytics/topics/page.tsx

4. **Implement Data Fetching Hooks:**
   - frontend/hooks/useAnalyticsOverview.ts - practice metrics
   - frontend/hooks/usePatientProgress.ts - patient progress
   - frontend/hooks/useSessionTrends.ts - trends over time
   - frontend/hooks/useTopicAnalytics.ts - topic frequencies

5. **Create Visualization Components:**
   - frontend/components/analytics/OverviewStatsCards.tsx - total patients/sessions, monthly trends
   - frontend/components/analytics/SessionTrendsChart.tsx - line chart showing sessions over time
   - frontend/components/analytics/TopicFrequencyChart.tsx - bar chart of topic frequencies
   - frontend/components/analytics/PatientProgressCard.tsx - individual patient metrics
   - frontend/components/analytics/TopicCooccurrenceHeatmap.tsx - topic relationships

6. **Implement Time Range Filters:**
   - Week, Month, Quarter, Year selectors
   - Date range picker for custom ranges

7. **Add Export Functionality:**
   - Export analytics data as CSV
   - Generate PDF reports (integrate with Feature 7 export when ready)

**Communication Protocol:**
- Wait for Orchestrator 3 to complete core integration testing
- Share chart component patterns for reuse in other features
- Test with real backend data

**Success Criteria:**
- Analytics dashboard displays real data from backend
- Charts render correctly with responsive design
- Time range filters update data correctly
- No performance issues with large datasets
- Export to CSV works
- Mobile-friendly layout

**Report Format:**
When complete, provide:
- Implementation summary
- Screenshots of analytics dashboard
- Chart component documentation
- Performance metrics
```

---

### Orchestrator 5: Patient Portal Specialist

```
Replace mock data in patient portal with real backend API integration.

**Context from Research:**
- Patient portal exists: frontend/app/patient/page.tsx
- Currently uses mock data (hardcoded sessions and strategies)
- Backend endpoints exist:
  - GET /api/patients/me (get current patient)
  - GET /api/sessions/?patient_id={current_user_id}
  - GET /api/v1/goals/?patient_id={current_user_id}
  - GET /api/v1/goals/{id}/progress

**Your Mission:**

1. **WAIT for Orchestrator 3** to complete core integration testing

2. **Create Patient Data Hooks:**
   - frontend/hooks/useCurrentPatient.ts - fetches logged-in patient data
   - frontend/hooks/usePatientSessions.ts - fetches patient's own sessions
   - frontend/hooks/usePatientGoals.ts - fetches patient's goals
   - frontend/hooks/useGoalProgress.ts - fetches progress for a goal

3. **Update Patient Portal Page:**
   - Modify frontend/app/patient/page.tsx
   - Replace mock data with real hooks
   - Display real session summaries (patient_summary, NOT therapist_notes)
   - Show active strategies from extracted notes
   - Display action items from sessions
   - Show goal progress charts

4. **Implement Patient Features:**
   - View session summaries (no access to full clinical notes)
   - Track action items (mark as complete)
   - View mood trends over time
   - See active strategies
   - View goal progress
   - Self-report progress updates (if Feature 6 supports it)

5. **Add Patient Navigation:**
   - frontend/app/patient/sessions/page.tsx - Session history
   - frontend/app/patient/goals/page.tsx - Goal tracking
   - frontend/app/patient/progress/page.tsx - Progress visualization

6. **Create Patient Components:**
   - frontend/components/patient/SessionSummaryCard.tsx
   - frontend/components/patient/GoalProgressCard.tsx
   - frontend/components/patient/ActionItemList.tsx

7. **Security Verification:**
   - Verify patient CANNOT access therapist_notes
   - Verify patient can ONLY see their own data
   - Test authorization with different patient accounts

**Communication Protocol:**
- Wait for Orchestrator 3 to complete core integration testing
- Test with real patient accounts
- Verify data isolation works correctly

**Success Criteria:**
- Patient portal displays real data from backend
- Patients only see patient_summary (not therapist_notes)
- Patients can only access their own sessions/goals
- Action item tracking works
- Goal progress displays correctly
- No security leaks (can't access other patients' data)

**Report Format:**
When complete, provide:
- Implementation summary
- Screenshots of patient portal with real data
- Security verification results
- Test results
```

---

### Orchestrator 6: Email Verification Specialist

```
Implement complete email verification system for Feature 1.

**Context from Research:**
- User model has is_verified field (defaults to false)
- No email sending implementation exists
- No verification token system exists
- Email verification not enforced

**Your Mission:**

1. **Add Email Service:**
   - Choose email provider: SendGrid, AWS SES, or SMTP
   - Add environment variables: EMAIL_PROVIDER, EMAIL_API_KEY, EMAIL_FROM
   - Create EmailService class (backend/app/services/email_service.py)
   - Implement send_email() method with template support

2. **Create Verification Token System:**
   - Generate secure verification tokens (JWT or UUID + hash)
   - Create database table: EmailVerification (user_id, token, expires_at)
   - Tokens expire after 24 hours
   - Create verify_email(token) endpoint

3. **Update Signup Flow:**
   - Modify backend/app/auth/router.py signup endpoint
   - After user registration, generate verification token
   - Send verification email with link: http://frontend/auth/verify?token={token}
   - User account remains is_verified=false until verified
   - Optional: Require verification before login (configurable)

4. **Add Verification Endpoints:**
   - POST /api/v1/auth/verify-email (verify token)
   - POST /api/v1/auth/resend-verification (resend email)
   - GET /api/v1/auth/verify-status (check if verified)

5. **Create Email Templates:**
   - backend/app/templates/emails/verification.html - Welcome email with verification link
   - backend/app/templates/emails/verification_success.html - Verification success email
   - (Bonus) backend/app/templates/emails/password_reset.html - Password reset email

6. **Frontend Integration:**
   - Create frontend/app/auth/verify/page.tsx
   - Handle token validation
   - Show success/error messages
   - Redirect to login after verification

7. **Add Configuration:**
   - REQUIRE_EMAIL_VERIFICATION env var (default: true in production)
   - Skip verification in development mode

**Files to Create:**
- backend/app/services/email_service.py (NEW)
- backend/app/routers/email_verification.py (NEW)
- backend/app/models/email_verification.py (NEW)
- backend/alembic/versions/xxx_add_email_verification.py (NEW migration)
- backend/app/templates/emails/verification.html (NEW)
- frontend/app/auth/verify/page.tsx (NEW)

**Files to Modify:**
- backend/app/auth/router.py (send email on signup, optionally enforce verification on login)
- backend/requirements.txt (add email library: sendgrid or boto3)
- backend/.env.example (add email config)
- frontend/.env.local.example (add verification page URL)

**Success Criteria:**
- Signup sends verification email
- Verification link validates token and marks user as verified
- Expired tokens rejected (24h expiration)
- Resend verification works
- Email templates look professional
- Frontend verification page works
- Can toggle requirement via env var

**Communication Protocol:**
- Notify Orchestrator 3 when email verification is ready for E2E testing

**Report Format:**
When complete, provide:
- Implementation summary
- Email provider chosen and setup instructions
- Sample verification email screenshot
- Test results
- Configuration guide
```

---

### Orchestrator 7: Test Suite Specialist

```
Debug and fix the 7 failing Feature 8 security tests.

**Context from Research:**
- 25/32 security tests passing (78.1%)
- 7 E2E auth flow tests failing
- Core functionality verified working
- Test report: backend/FEATURE_8_TEST_REPORT.md

**Failing Tests (from research):**

1. test_security_headers_on_500_errors - Exception handling issue
2. test_complete_mfa_enrollment_flow - 401 (no auth token)
3. test_session_management_flow - 401 (no auth token)
4. test_audit_trail_created - 401 (no auth token)
5. test_consent_workflow - DetachedInstanceError (session management)
6. test_emergency_access_workflow - ObjectDeletedError (cascade delete)
7. test_complete_security_integration - OperationalError (no such table: users)

**Your Mission:**

1. **Analyze Test Failures:**
   - Run: cd backend && pytest tests/security/ tests/e2e/test_security_flow.py -v
   - Identify exact error for each of 7 tests
   - Read test output and error messages
   - Determine root cause for each failure

2. **Fix Authentication Issues (6 tests):**
   - Create authenticated_client fixture in backend/tests/conftest.py:
     ```python
     @pytest.fixture
     def authenticated_client(client, test_therapist_security):
         response = client.post("/api/v1/auth/login", json={
             "email": test_therapist_security.email,
             "password": "SecurePass123!@"
         })
         token = response.json()["access_token"]
         client.headers["Authorization"] = f"Bearer {token}"
         return client
     ```
   - Update E2E tests to use authenticated_client instead of client

3. **Fix Database Session Management (2 tests):**
   - Add expire_on_commit=False to test session configuration
   - Use session.refresh(user) before accessing user attributes
   - Use joinedload/selectinload for eager loading relationships

4. **Fix Test Database Initialization (1 test):**
   - Ensure Base.metadata.create_all(bind=engine) called in test setup
   - Verify all models imported before creating tables

5. **Fix 500 Error Handler (1 test):**
   - Add exception handler to test app fixture
   - Update test to verify headers present on 500 responses

6. **Verify Fixes:**
   - Run full security test suite: pytest tests/security/ -v
   - Run all backend tests: pytest backend/tests/ -v
   - Ensure no regressions in other test files

7. **Update Test Report:**
   - Update backend/FEATURE_8_TEST_REPORT.md with results
   - Document any implementation changes made
   - Add test execution instructions

**Files to Analyze:**
- backend/tests/security/test_mfa.py
- backend/tests/security/test_consent.py
- backend/tests/security/test_encryption.py
- backend/tests/security/test_emergency.py
- backend/tests/security/test_sessions.py
- backend/tests/security/test_audit.py
- backend/tests/e2e/test_security_flow.py
- backend/tests/conftest.py (fixtures)

**Files to Modify:**
- backend/tests/conftest.py (add authenticated_client, fix session config)
- backend/tests/e2e/test_security_flow.py (use authenticated_client)
- backend/tests/middleware/test_security_headers.py (exception handler)
- backend/FEATURE_8_TEST_REPORT.md (update results)

**Communication Protocol:**
- If auth issues found, coordinate with Orchestrator 2 (MFA specialist)
- Share findings with all orchestrators to prevent similar issues

**Success Criteria:**
- All 32 security tests passing (100%)
- No regressions in other test suites
- Test execution time reasonable (< 2 minutes total)
- Tests properly isolated (can run in any order)
- Test report updated with 32/32 passing

**Report Format:**
When complete, provide:
- Root cause analysis for each failing test
- Implementation changes made (if any)
- Test changes made
- Final test results (32/32 passing)
- Lessons learned document
```

---

## 🚀 EXECUTION INSTRUCTIONS

### Step 1: Create Tracking Infrastructure

```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj"

# Create progress tracking file
cat > ORCHESTRATOR_PROGRESS.md << 'EOF'
# Orchestrator Progress Tracker

## Orchestrator 1: Export Implementation
- Status: PENDING
- Progress: 0%
- Blockers: None
- ETA: 90 minutes

## Orchestrator 2: MFA Integration
- Status: PENDING
- Progress: 0%
- Blockers: None
- ETA: 60 minutes

## Orchestrator 3: Frontend Integration Testing
- Status: WAITING
- Progress: 0%
- Dependencies: Orchestrator 2 (MFA)
- Blockers: Waiting for MFA integration
- ETA: Start after Orchestrator 2

## Orchestrator 4: Analytics Dashboard
- Status: WAITING
- Progress: 0%
- Dependencies: Orchestrator 3
- Blockers: Waiting for integration testing
- ETA: Start after Orchestrator 3

## Orchestrator 5: Patient Portal
- Status: WAITING
- Progress: 0%
- Dependencies: Orchestrator 3
- Blockers: Waiting for integration testing
- ETA: Start after Orchestrator 3

## Orchestrator 6: Email Verification
- Status: PENDING
- Progress: 0%
- Blockers: None
- ETA: 120 minutes

## Orchestrator 7: Test Suite Fixes
- Status: PENDING
- Progress: 0%
- Blockers: None
- ETA: 90 minutes
EOF

# Commit tracking file
git add ORCHESTRATOR_PROGRESS.md
git commit -m "Add meta-orchestration capability: Track 7 parallel orchestrators"
```

### Step 2: Execute Orchestration

Use this prompt to execute in a fresh context window:

```
/cl:orchestrate Execute TherapyBridge MVP completion with 7 parallel orchestrators per ORCHESTRATION_CONTINUATION_PROMPT.md
```

### Step 3: Monitor Progress

The master orchestrator will:
1. Read ORCHESTRATOR_PROGRESS.md
2. Spawn Wave 1 orchestrators (1, 2, 6, 7) in parallel
3. Monitor their progress
4. When Orchestrator 2 completes, spawn Orchestrator 3
5. When Orchestrator 3 completes, spawn Orchestrators 4 & 5 in parallel
6. Aggregate results
7. Run final integration tests
8. Generate MVP readiness report

---

## 📊 SUCCESS METRICS

### Individual Orchestrator Success
Each orchestrator must achieve:
- ✅ All assigned tasks completed
- ✅ Tests written and passing
- ✅ Code reviewed and documented
- ✅ Integration points verified
- ✅ Dependencies satisfied or notified
- ✅ Progress tracking updated

### Overall Mission Success
The master orchestrator achieves success when:
- ✅ All 7 orchestrators complete their tasks
- ✅ All features integrated and working together
- ✅ All backend tests passing (32/32 security tests + all others)
- ✅ All frontend pages functional
- ✅ End-to-end user flows work (signup → login → upload → view → export)
- ✅ MFA login works
- ✅ Analytics displays real data
- ✅ Patient portal connected to API
- ✅ Email verification works
- ✅ Export generates files
- ✅ No blocking bugs or issues
- ✅ MVP ready for deployment

---

## 📝 EXPECTED DELIVERABLES

At the end of this mission, TherapyBridge will have:

1. ✅ **Feature 7:** Export background processing working (PDF/DOCX generation)
2. ✅ **Feature 1:** MFA two-step login flow complete
3. ✅ **Frontend:** Full E2E integration test suite
4. ✅ **Frontend:** Analytics dashboard implemented with charts
5. ✅ **Frontend:** Patient portal connected to real API
6. ✅ **Feature 1:** Email verification system working
7. ✅ **Feature 8:** All 32 security tests passing (100%)
8. ✅ **Documentation:** Updated test reports and integration guides
9. ✅ **Deployment:** MVP ready for AWS Lambda + Vercel deployment

---

## 🔗 USEFUL FILE REFERENCES

**Research Documentation (created in Wave 0):**
- `COMPLETE_CODEBASE_MAP.txt` - Full codebase structure
- `CODEBASE_QUICK_REFERENCE.txt` - Quick facts and key files
- `CODEBASE_EXPLORATION_INDEX.md` - Navigation guide

**Feature Documentation:**
- `therabridge-backend/FEATURE_1_AUTH.md` - Auth feature spec
- `therabridge-backend/FEATURE_2_ANALYTICS.md` - Analytics spec
- `therabridge-backend/FEATURE_7_EXPORT.md` - Export spec
- `therabridge-backend/FEATURE_8_COMPLIANCE.md` - Security spec
- `backend/FEATURE_8_TEST_REPORT.md` - Test failure analysis

**Key Implementation Files:**
- `backend/app/routers/sessions.py:1154-1181` - Export placeholder
- `backend/app/auth/router.py:27-87` - Login endpoint
- `backend/app/routers/mfa.py:376-479` - MFA validation (complete)
- `backend/tests/conftest.py` - Test fixtures (1834 lines)
- `frontend/lib/api-client.ts` - API client with auto token refresh
- `frontend/app/patient/page.tsx` - Patient portal with mock data

---

**END OF CONTINUATION PROMPT**
**Last Updated:** 2025-12-18
**Backup Commit:** fdf6784
**Status:** Ready for execution ✅
