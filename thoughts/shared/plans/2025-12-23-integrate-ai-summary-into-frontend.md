# AI-Generated Summary Frontend Integration Plan

## Overview

Integrate the AI-generated short summary (Wave 1 topic extraction) from the backend into the frontend UI components. This will replace the hardcoded `patientSummary` field with real data fetched from the database.

## Current State Analysis

### Backend
- **API Endpoint**: `POST /api/sessions/{session_id}/extract-topics` (sessions.py:855)
- **Response Model**: `TopicExtractionResponse` with fields:
  - `summary` (max 150 characters)
  - `topics`, `action_items`, `technique`, `confidence`, `extracted_at`
- **Database Column**: `therapy_sessions.summary` (TEXT, line 10 in migration 003)
- **Auto-caching**: Prevents duplicate extractions (already implemented)

### Frontend
- **Current Implementation**:
  - `SessionCard.tsx:63` - Displays `session.patientSummary` (mock data)
  - `SessionDetail.tsx` - Also uses mock data
- **Session Type** (`lib/types.ts:213`): Does NOT include topic extraction fields
- **Existing Patterns**:
  - `useSession` hook uses SWR for data fetching
  - `api-client.ts` provides authenticated request handling
  - `/api/v1/sessions/{id}` endpoint returns `Session` object

### Key Discovery
The current `Session` TypeScript interface does not include the topic extraction fields (`summary`, `topics`, `action_items`, `technique`). We need to:
1. Extend the `Session` type to include these fields
2. Ensure the backend session GET endpoint returns these fields
3. Update frontend components to use the real data

## Desired End State

After implementation:
1. ✅ `Session` type includes topic extraction fields
2. ✅ Backend GET `/api/v1/sessions/{id}` returns topic extraction data
3. ✅ `SessionCard` component displays AI-generated `summary` from database
4. ✅ `SessionDetail` component displays AI-generated `summary` from database
5. ✅ No hardcoded mock data for summaries

### Verification
- Open patient dashboard, see real AI-generated summaries in session cards
- Click session card to open detail view, see same summary
- Verify summary updates when backend data changes
- Check that missing summaries gracefully show fallback text

## What We're NOT Doing

- ❌ Triggering extraction from frontend (user will set up pipeline later)
- ❌ Creating new API endpoints (will use existing GET session endpoint)
- ❌ Building extraction UI controls (just display for now)
- ❌ Handling extraction progress/loading states (assumes already extracted)
- ❌ Re-extracting on every fetch (relies on backend caching)

## Implementation Approach

Three-phase approach:
1. **Backend Enhancement** - Ensure GET session endpoint returns topic extraction fields
2. **Type System Update** - Extend TypeScript types to include new fields
3. **UI Component Integration** - Update components to use real data

---

## Phase 1: Backend Session Endpoint Enhancement

### Overview
Ensure the GET `/api/v1/sessions/{id}` endpoint returns topic extraction fields alongside session data.

### Changes Required

#### 1.1 Update Session Response Schema

**File**: `backend/app/routers/sessions.py`
**Changes**: Find the GET session endpoint response model

**Current behavior**: Need to verify if `SessionResponse` includes topic extraction fields.

**Required fields in response:**
```python
class SessionResponse(BaseModel):
    # ... existing fields ...

    # Topic extraction fields (from Wave 1)
    summary: Optional[str] = None  # Ultra-brief summary (max 150 chars)
    topics: Optional[List[str]] = None  # 1-2 main topics
    action_items: Optional[List[str]] = None  # 2 action items
    technique: Optional[str] = None  # Primary therapeutic technique
    extraction_confidence: Optional[float] = None  # 0.0 to 1.0
    topics_extracted_at: Optional[datetime] = None
```

**Investigation needed:**
- Check if `SessionResponse` already includes these fields
- If not, add them to the response model
- Ensure the database query in `get_session()` selects these columns

#### 1.2 Verify Database Query Includes Fields

**File**: `backend/app/routers/sessions.py`
**Changes**: Find the GET session endpoint implementation

**Required SELECT fields:**
```python
# Ensure query includes:
.select("""
    *,
    summary,
    topics,
    action_items,
    technique,
    extraction_confidence,
    topics_extracted_at
""")
```

**Implementation approach:**
- If using `.select("*")`, the fields should already be included
- If using explicit field list, add the topic extraction fields
- Verify with a test API call

### Success Criteria

#### Automated Verification:
- [x] Backend server starts without errors: `uvicorn app.main:app --reload`
- [x] OpenAPI schema includes topic extraction fields: `http://localhost:8000/docs`
- [x] Type checking passes: `python3 -m py_compile app/routers/sessions.py`

#### Manual Verification:
- [ ] Call `GET /api/v1/sessions/{id}` with curl/Postman
- [ ] Verify response includes `summary`, `topics`, `action_items`, `technique`
- [ ] Check that `null` values are returned for sessions without extraction
- [ ] Verify sessions with extraction show the correct data

**Implementation Note**: Pause here and verify the backend returns the correct fields before proceeding to Phase 2.

---

## Phase 2: Frontend Type System Update

### Overview
Extend the TypeScript `Session` interface to include topic extraction fields and ensure type safety across the frontend.

### Changes Required

#### 2.1 Update Session Interface

**File**: `frontend/lib/types.ts`
**Changes**: Add topic extraction fields to `Session` interface (around line 213)

**Before:**
```typescript
export interface Session {
  readonly id: string;
  readonly patient_id: string;
  readonly therapist_id: string;
  readonly session_date: string;
  readonly duration_seconds: number | null;
  readonly audio_filename: string | null;
  readonly audio_url: string | null;
  readonly transcript_text: string | null;
  readonly transcript_segments: ReadonlyArray<TranscriptSegment> | null;
  readonly extracted_notes: ExtractedNotes | null;
  readonly status: SessionStatus;
  readonly error_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
  readonly processed_at: string | null;
}
```

**After:**
```typescript
export interface Session {
  readonly id: string;
  readonly patient_id: string;
  readonly therapist_id: string;
  readonly session_date: string;
  readonly duration_seconds: number | null;
  readonly audio_filename: string | null;
  readonly audio_url: string | null;
  readonly transcript_text: string | null;
  readonly transcript_segments: ReadonlyArray<TranscriptSegment> | null;
  readonly extracted_notes: ExtractedNotes | null;
  readonly status: SessionStatus;
  readonly error_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
  readonly processed_at: string | null;

  // Wave 1 AI Analysis - Topic Extraction
  readonly summary: string | null;  // Ultra-brief summary (max 150 chars)
  readonly topics: ReadonlyArray<string> | null;  // 1-2 main topics
  readonly action_items: ReadonlyArray<string> | null;  // 2 action items
  readonly technique: string | null;  // Primary therapeutic technique
  readonly extraction_confidence: number | null;  // 0.0 to 1.0
  readonly topics_extracted_at: string | null;  // ISO timestamp
}
```

**Reasoning**:
- All fields are `readonly` (consistent with existing pattern)
- All fields are nullable (sessions may not have extraction yet)
- Arrays use `ReadonlyArray<T>` (matches `transcript_segments` pattern)
- Timestamps use `string` (ISO format, matches existing pattern)

### Success Criteria

#### Automated Verification:
- [x] TypeScript compilation passes: `npm run build` (in frontend/)
- [x] Type checking passes: `npm run typecheck` (if available)
- [x] No new ESLint errors: `npm run lint`

#### Manual Verification:
- [x] Review git diff to confirm only `Session` interface changed
- [x] Verify no breaking changes to existing code
- [x] Check that IDE autocomplete shows new fields

**Implementation Note**: After type updates, verify no TypeScript errors before proceeding to Phase 3.

---

## Phase 3: UI Component Integration

### Overview
Update `SessionCard` and `SessionDetail` components to display the AI-generated `summary` field instead of mock `patientSummary`.

### Changes Required

#### 3.1 Update SessionCard Component

**File**: `frontend/app/patient/components/SessionCard.tsx`
**Changes**: Replace `patientSummary` usage with `summary` field (line 63)

**Before:**
```typescript
// Extract summary from patientSummary (first 200 chars)
const summary = session.patientSummary || 'Session summary not available.';
```

**After:**
```typescript
// Extract summary from AI-generated Wave 1 analysis
const summary = session.summary || 'Summary not yet generated.';
```

**Reasoning**:
- `session.summary` is now properly typed (from Phase 2)
- Fallback message indicates summary hasn't been extracted yet
- No other changes needed (component already handles null gracefully)

**Optional Enhancement** (if you want to show extraction status):
```typescript
// Show extraction confidence if available
const summary = session.summary
  ? `${session.summary}${session.extraction_confidence ? ` (${Math.round(session.extraction_confidence * 100)}% confidence)` : ''}`
  : 'Summary not yet generated.';
```

#### 3.2 Update SessionDetail Component

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Changes**: Find where `patientSummary` is used and replace with `summary`

**Investigation needed:**
- Locate the line displaying summary in detail view
- Replace with `session.summary` field
- Ensure fallback text is appropriate

**Example expected change:**
```typescript
// Before
<p>{session.patientSummary}</p>

// After
<p>{session.summary || 'Summary not yet generated.'}</p>
```

#### 3.3 Remove Mock Data Reference (Dashboard v3)

**File**: Check if dashboard-v3 uses a different Session type
**Changes**: If there's a separate mock data structure for dashboard v3, update it too

**Files to check:**
- `frontend/app/patient/dashboard-v3/lib/mockData.ts` (if exists)
- `frontend/app/patient/lib/types.ts` (dashboard-specific types)
- `frontend/app/patient/lib/usePatientSessions.ts` (data hook)

**Note**: Based on file search, dashboard v3 likely uses the same `Session` type, so changes from Phase 2 should propagate automatically.

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compilation passes: `npm run build`
- [ ] No console errors when running dev server: `npm run dev`
- [ ] Components render without errors

#### Manual Verification:
- [ ] Start frontend: `npm run dev`
- [ ] Navigate to patient dashboard
- [ ] Verify SessionCard displays AI-generated summary (or fallback if not extracted)
- [ ] Click on a session card to open SessionDetail
- [ ] Verify same summary appears in detail view
- [ ] Test with different sessions (with and without extractions)
- [ ] Check responsive design still works (summary wraps correctly)

**Implementation Note**: Test with both extracted and non-extracted sessions to ensure graceful degradation.

---

## Phase 4: Optional Enhancements (Future)

### Overview
Enhancements that can be added later after basic integration is working.

### Potential Enhancements

#### 4.1 Display Additional Topic Extraction Fields

**Show topics, action items, and technique in SessionCard:**
```typescript
{session.topics && session.topics.length > 0 && (
  <div className="flex gap-2 flex-wrap">
    {session.topics.map((topic, i) => (
      <span key={i} className="px-2 py-1 bg-teal-100 dark:bg-teal-900 rounded-full text-xs">
        {topic}
      </span>
    ))}
  </div>
)}
```

#### 4.2 Confidence Score Indicator

**Visual indicator for extraction quality:**
```typescript
{session.extraction_confidence !== null && (
  <div className="flex items-center gap-1 text-xs text-muted-foreground">
    <span>Confidence:</span>
    <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
      <div
        className="h-full bg-teal-500"
        style={{ width: `${session.extraction_confidence * 100}%` }}
      />
    </div>
  </div>
)}
```

#### 4.3 Extraction Timestamp

**Show when summary was generated:**
```typescript
{session.topics_extracted_at && (
  <p className="text-xs text-muted-foreground">
    Analyzed {formatDistanceToNow(new Date(session.topics_extracted_at))} ago
  </p>
)}
```

#### 4.4 Manual Re-extraction Button

**Allow therapists to trigger re-extraction:**
```typescript
<button
  onClick={() => extractTopics(session.id)}
  className="text-xs underline"
>
  Re-analyze session
</button>
```

**Note**: These are optional and can be implemented later. For now, just displaying the summary is sufficient.

---

## Testing Strategy

### Backend API Testing

**Test GET session endpoint:**
```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# In another terminal, test API
curl -X GET "http://localhost:8000/api/v1/sessions/{session_id}" \
  -H "Authorization: Bearer {token}"

# Expected response includes:
{
  "id": "...",
  "summary": "Patient discussed anxiety triggers...",
  "topics": ["anxiety", "coping strategies"],
  "action_items": ["Practice box breathing", "Journal daily"],
  "technique": "Cognitive Restructuring",
  "extraction_confidence": 0.92,
  "topics_extracted_at": "2025-12-23T12:34:56Z",
  ...
}
```

### Frontend Integration Testing

**Test SessionCard component:**
1. Start frontend: `cd frontend && npm run dev`
2. Navigate to patient dashboard
3. Check each session card for summary display
4. Verify fallback text appears for non-extracted sessions
5. Verify summary wraps correctly (max 150 chars fits within card)

**Test SessionDetail component:**
1. Click on a session card
2. Verify detail view opens
3. Check that summary matches the card summary
4. Test with multiple sessions

**Test responsive behavior:**
1. Open browser DevTools
2. Test mobile viewport (375px)
3. Test tablet viewport (768px)
4. Test desktop viewport (1920px)
5. Verify summary text wraps gracefully at all sizes

### Edge Case Testing

**Test scenarios:**
- Session with no extraction (`summary: null`) → shows fallback
- Session with empty summary (`summary: ""`) → shows fallback
- Session with very long summary (>150 chars) → should not happen (backend enforces), but test graceful truncation
- Session with special characters in summary → verify proper HTML escaping
- Session with extraction confidence = 0 → still displays summary

### Manual Testing Steps

1. **Test with existing mock data** (no backend required):
   - Temporarily add `summary: "Test AI summary here"` to mock session data
   - Verify it displays correctly

2. **Test with real backend** (requires running backend):
   - Use a session that has been through topic extraction
   - Verify real data displays correctly

3. **Test graceful degradation**:
   - Use a session without extraction
   - Verify fallback message appears
   - Ensure UI doesn't break

## Performance Considerations

### Negligible Performance Impact

**Why this is efficient:**
- No additional API calls (summary comes with existing session fetch)
- No client-side computation (just display)
- Existing SWR caching prevents redundant requests
- `useSession` hook already handles intelligent polling

**Expected overhead:** <1ms (just rendering text)

### Potential Future Optimizations

**If performance becomes an issue later:**
- Add GraphQL fragments to fetch only needed fields
- Implement field-level caching
- Add optimistic updates for manual re-extraction

**Current approach is optimal** because:
- Session data is already being fetched
- Summary is a small text field (~150 chars)
- No additional network requests needed

## Migration Notes

### No Database Migration Needed

**Why:**
- Database schema already has `summary` column (migration 003)
- Backend endpoint changes are additive (won't break existing clients)
- Frontend type changes are compile-time only

### Deployment Steps

1. **Deploy backend changes** (if any needed for GET endpoint)
   - Update session response model to include extraction fields
   - Restart backend server
   - Verify with curl test

2. **Deploy frontend changes**
   - Update `Session` type definition
   - Update `SessionCard` and `SessionDetail` components
   - Build and deploy: `npm run build`
   - Verify in production

3. **Gradual rollout** (optional):
   - Feature flag to toggle between mock and real summaries
   - Monitor for errors
   - Enable for all users once stable

### Rollback Plan

**If issues occur:**
1. Frontend: Revert to using `patientSummary` mock data
2. Backend: No rollback needed (additive changes)
3. Database: No changes made (schema already exists)

## References

- Backend API endpoint: `backend/app/routers/sessions.py:855` (POST extract-topics)
- Backend schema: `supabase/migrations/003_add_topic_extraction.sql:10`
- Frontend Session type: `frontend/lib/types.ts:213`
- SessionCard component: `frontend/app/patient/components/SessionCard.tsx:63`
- Topic extraction plan: `thoughts/shared/plans/2025-12-23-session-summary-150-char-limit.md`
- Wave 1 analysis: `backend/app/services/topic_extractor.py:209` (summary generation)

## User Requirements Summary

From user responses:
1. **Display locations**: Both SessionCard and SessionDetail
2. **Data replacement**: Replace `patientSummary` with AI-generated `summary`
3. **Extraction timing**: Automatic (pipeline setup later, just test display now)
4. **Architecture**: Use existing patterns (SWR + api-client)
5. **Data source**: Always fetch from database (no on-demand extraction from frontend)

---

## Next Steps After Implementation

1. Verify summary displays correctly in UI
2. Test with sessions that have and haven't been extracted
3. Set up automatic extraction pipeline (separate task)
4. Consider adding topics/action items to UI (Phase 4 enhancements)
5. Gather user feedback on summary quality and usefulness
