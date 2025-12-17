# Form Validation Audit - Executive Summary

## Quick Overview

This audit analyzed form validation across the **TherapyBridge** application, checking for consistency between client-side (React) and server-side (FastAPI/Pydantic) validation.

**Overall Score: 64% Coverage | 57% Security | 67% Data Integrity**

---

## Key Findings

### What's Working Well ✓

1. **Authentication (Signup)**
   - Email format validation (Pydantic EmailStr)
   - Email uniqueness enforcement
   - Password minimum length (8 chars)
   - Rate limiting (3/hour for signup)
   - Duplicate email detection with IntegrityError handling

2. **Rate Limiting**
   - Signup: 3 requests/hour per IP
   - Login: 5 requests/minute per IP
   - Properly prevents brute force and spam

3. **Enum Validation**
   - UserRole, SessionStatus, MoodLevel enums properly validated
   - Frontend dropdowns prevent invalid enum values

4. **Error Handling**
   - API client correctly reads error.detail field
   - Errors propagate properly from backend to frontend
   - Error display works correctly in UI

### Critical Issues ✗

1. **File Upload Validation Missing**
   - MAX_FILE_SIZE = 100MB defined but NEVER CHECKED
   - No MIME type validation (only extension)
   - Can upload non-audio files with .mp3 extension
   - No patient existence verification
   - **Risk:** DOS attacks via large files, storage exhaustion

2. **Password Strength Not Enforced**
   - Allows passwords like "12345678" (8 digits, no letters)
   - No uppercase/lowercase/special char requirements
   - No frontend strength indicator
   - **Risk:** Weak passwords compromise account security

3. **Patient Data Validation Missing**
   - Patient name: no length validation (could be whitespace only)
   - Patient email: not validated when provided
   - Patient phone: no format validation
   - **Risk:** Garbage data in database, poor UX

4. **Extracted Notes Constraints Not Enforced**
   - Schema descriptions say "3-7 topics" but no validation
   - Descriptions say "2-3 sentence" but no length check
   - Mood trajectory should be enum, not string
   - Risk flag severity should be enum, not string
   - **Risk:** AI output inconsistency, hard to debug

### High Priority Issues

1. **Login Form Missing Frontend Validation**
   - Inconsistent with signup form
   - No password length check before API call
   - No email validation
   - **Risk:** Poor UX, unexpected server errors

2. **File Upload UI Missing**
   - No frontend file validation feedback
   - Can't catch file type/size issues before upload
   - No progress indicator
   - **Risk:** Poor UX, wasted bandwidth

3. **Patient Creation Form Not Implemented**
   - Form doesn't exist yet
   - No validation planned
   - **Risk:** Future work will need validation retrofit

---

## Detailed Findings by Area

### 1. Authentication

**Signup Form**
- Frontend validation: Password min 8 ✓ | Email type="email" ✓ | Full name required only
- Backend validation: Email format ✓ | Email unique ✓ | Password min 8 ✓ | Full name min 1 ✓
- Gap: Password strength not enforced, full name format not validated

**Login Form**
- Frontend validation: None ✗
- Backend validation: Email format ✓ | Password verified ✓ | Account active ✓
- Gap: Frontend has no validation (inconsistent with signup)

**Issue:** Frontend login form should at least check email format and password length before sending to API.

### 2. Session Upload

**Current State**
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # Defined but never checked!
if file_ext not in allowed_extensions:  # Extension checked ✓
    raise HTTPException(...)
# ✗ File size NOT checked
# ✗ MIME type NOT checked
# ✗ Patient existence NOT checked
```

**Risks**
1. User can upload 1GB file, causing storage/memory issues
2. User can rename .txt file to .mp3 and upload
3. User can create orphaned sessions (patient doesn't exist)
4. No way to prevent abuse without file size limit

**Fix (5 lines of code)**
```python
# After file extension check, add:
if file.size and file.size > MAX_FILE_SIZE:
    raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE/1024/1024}MB")

if file.content_type not in {'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm'}:
    raise HTTPException(400, f"Invalid audio type: {file.content_type}")

# Before creating session, add:
patient = await db.execute(select(db_models.Patient).where(...))
if not patient.scalar_one_or_none():
    raise HTTPException(404, "Patient not found")
```

### 3. Patient Creation

**Current State (No Frontend Form Yet)**
```python
class PatientBase(BaseModel):
    name: str  # ✗ No length validation
    email: Optional[str] = None  # ✗ No format validation
    phone: Optional[str] = None  # ✗ No format validation
```

**Missing**
- Min/max length on name (should be 1-200 chars)
- Email format validation (EmailStr)
- Phone format validation (international format)
- Duplicate name checking
- Therapist existence verification

**Impact:** When patient creation form is built, validation will be missing.

### 4. Extracted Notes (AI Output)

**Documented Constraints (Not Enforced)**
```python
key_topics: List[str] = Field(..., description="Main subjects discussed (3-7 items)")
# Description says 3-7 but no: min_items=3, max_items=7

topic_summary: str = Field(..., description="2-3 sentence overview")
# Description says 2-3 sentence but no: min_length, max_length

mood_trajectory: str = Field(...)  # Should be enum
risk_flags: List[RiskFlag] = ...  # RiskFlag.severity should be enum
```

**Issue:** Descriptions are documentation only. Pydantic doesn't enforce them.

**Fix:** Add constraints to Field definitions
```python
key_topics: List[str] = Field(..., min_items=3, max_items=7, description="...")
topic_summary: str = Field(..., min_length=10, max_length=500, description="...")

class MoodTrajectory(str, Enum):
    improving = "improving"
    declining = "declining"
    stable = "stable"
    fluctuating = "fluctuating"

mood_trajectory: MoodTrajectory

class RiskFlagSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class RiskFlag(BaseModel):
    type: str
    evidence: str
    severity: RiskFlagSeverity  # Now enforced
```

---

## Files to Review

### Backend
- `/backend/app/auth/schemas.py` - Auth validation rules
- `/backend/app/auth/router.py` - Auth business logic
- `/backend/app/routers/sessions.py` - **Session upload validation (CRITICAL GAPS)**
- `/backend/app/routers/patients.py` - Patient creation
- `/backend/app/models/schemas.py` - Data models

### Frontend
- `/frontend/app/auth/signup/page.tsx` - Signup form
- `/frontend/app/auth/login/page.tsx` - **Login form (missing validation)**
- `/frontend/lib/auth-context.tsx` - Auth state management
- `/frontend/lib/api-client.ts` - API communication (error handling is correct)

---

## Implementation Priority

### Phase 1: Security (Do First - 30 minutes)
1. Add file size validation to sessions.py
2. Add MIME type validation to sessions.py
3. Add patient existence check to sessions.py
4. Add password strength validation to auth/schemas.py
5. Run security tests on all three

### Phase 2: Data Integrity (1 hour)
1. Add string length constraints to PatientBase
2. Enforce ExtractedNotes field constraints
3. Convert status fields to proper enums
4. Add email format validation where optional

### Phase 3: UX/Frontend (1-2 hours)
1. Add file upload validation hook
2. Add password strength indicator to signup
3. Add login form validation (matching signup)
4. Create patient creation form with full validation

### Phase 4: Testing & Polish (1-2 hours)
1. Write validation test suite
2. Add form validation library (zod or react-hook-form)
3. Create validation documentation
4. Test error messages end-to-end

---

## Testing Checklist

- [ ] Signup with invalid email (e.g., "not-email")
- [ ] Signup with password < 8 characters
- [ ] Signup with duplicate email
- [ ] Signup with whitespace-only full name
- [ ] Login with correct credentials
- [ ] Login with wrong password
- [ ] Upload file > 100MB
- [ ] Upload .txt file renamed to .mp3
- [ ] Upload without selecting file
- [ ] Upload to non-existent patient
- [ ] Create patient with empty name
- [ ] Create patient with invalid email
- [ ] Create patient with invalid phone
- [ ] Verify error messages match between frontend and backend

---

## Risk Summary

| Area | Current | Risk | Fix Time |
|------|---------|------|----------|
| Auth | Good | Low | N/A |
| File Upload | Poor | **CRITICAL** | 5 min |
| Patient Data | Poor | High | 10 min |
| Extracted Notes | Moderate | Medium | 15 min |
| Login Form | Fair | Medium | 5 min |
| Frontend Upload | None | Medium | 20 min |

---

## Generated Reports

1. **FORM_VALIDATION_ANALYSIS.md** - Comprehensive technical analysis
2. **VALIDATION_SUMMARY.txt** - Quick reference with line numbers
3. **VALIDATION_MATRIX.txt** - Visual coverage matrix
4. **VALIDATION_CODE_LOCATIONS.md** - Code examples and locations

---

## Next Steps

1. Review this summary and linked reports
2. Prioritize fixes based on risk/effort matrix
3. Implement Phase 1 security fixes first
4. Add tests for each fix
5. Update validation documentation
6. Consider form validation library for Phase 4

