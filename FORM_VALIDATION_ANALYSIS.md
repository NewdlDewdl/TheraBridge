# Form Validation Analysis: Frontend & Backend

## Executive Summary

The application has a **hybrid validation approach** with validation implemented at both frontend (React) and backend (FastAPI/Pydantic). However, there are significant **consistency gaps** and **missing server-side validation** that create security and UX risks.

### Validation Coverage Status
- **Signup**: ✓ Frontend + ✓ Backend (good)
- **Login**: ✓ Frontend + ✓ Backend (good)
- **Session Upload**: ✓ Backend only (file extension check exists)
- **Patient Creation**: ✗ Minimal validation (name length, email format not enforced)
- **Error Message Consistency**: ✗ Mismatch between client and server

---

## 1. Authentication Validation

### Backend Validation (app/auth/schemas.py)

```python
class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr  # Auto-validates email format
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    role: UserRole

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
```

**Backend Rules:**
- Email: EmailStr (validates format via pydantic-core)
- Password: min 8 characters
- Full Name: min 1 character
- Role: Must be enum value (therapist, patient, admin)

### Frontend Validation (frontend/app/auth/signup/page.tsx)

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');

  if (password.length < 8) {
    setError('Password must be at least 8 characters');
    return;
  }

  setIsLoading(true);

  try {
    await signup(email, password, fullName, role);
    // Redirect based on role
  } catch (err: any) {
    setError(err.message || 'Signup failed');
  }
};
```

**Frontend Rules:**
- Password: min 8 characters (checked)
- Email: type="email" (browser native validation only)
- Full Name: required attribute only (no length validation)
- Role: Select dropdown (enum guaranteed)

### Login Page (frontend/app/auth/login/page.tsx)

**Frontend Rules:**
- Email: type="email" (browser native validation)
- Password: required attribute only (no client-side length check)

## Findings

### Consistency Issues

| Field | Frontend | Backend | Gap |
|-------|----------|---------|-----|
| Email | Browser native validation | EmailStr (strict) | Browser allows invalid email patterns |
| Password (Signup) | min 8 | min 8 | ✓ Consistent |
| Password (Login) | None | EmailStr validated | ✗ No client check |
| Full Name | required only | min 1 | ✓ Acceptable |
| Role | Enum dropdown | UserRole enum | ✓ Consistent |

### Error Message Mismatch

**Backend error (app/auth/router.py):**
```python
# Line 53-54
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password"
)
```

**Frontend catch:**
```typescript
// Line 48-49
catch (err: any) {
  setError(err.message || 'Signup failed');
}
```

- Backend returns `detail` field, frontend expects `message` field
- Error display may fail silently or show "Signup failed" instead of actual error

### Backend Validation Coverage

**Implemented:**
- ✓ Email uniqueness (IntegrityError check, line 111-116)
- ✓ Email validation (EmailStr)
- ✓ Password requirements (min 8)
- ✓ Account status check (is_active)
- ✓ Rate limiting (5/min login, 3/hour signup)

**Missing:**
- ✗ Password strength rules (no uppercase, lowercase, special char checks)
- ✗ Full name format validation (accepts whitespace-only strings)
- ✗ Account deactivation prevents login but no rate limit reset

---

## 2. Session Upload Validation

### Backend Validation (backend/app/routers/sessions.py)

```python
@router.post("/upload", response_model=SessionResponse)
async def upload_audio_session(
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    # Check file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"File type {file_ext} not supported. Allowed: {allowed_extensions}")
```

**Backend Rules:**
- Filename must be provided
- File extension must be in allowed list
- MAX_FILE_SIZE = 100MB (defined but not enforced in code)

**Missing:**
- ✗ File size validation (MAX_FILE_SIZE is defined but never checked)
- ✗ File MIME type validation (only extension checked)
- ✗ Patient ID validation (no check if patient exists or belongs to therapist)
- ✗ Audio file format validation (doesn't verify it's actually audio)

### Frontend Validation

**Currently Missing:**
- ✗ No file size pre-check before upload
- ✗ No file type validation
- ✗ No error handling display for upload failures
- ✗ No user feedback on file selection

---

## 3. Patient Creation Validation

### Backend Validation (backend/app/models/schemas.py)

```python
class PatientBase(BaseModel):
    """Base patient data"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class PatientCreate(PatientBase):
    """Request to create a new patient"""
    therapist_id: UUID
```

**Backend Rules:**
- Name: Required string (NO length validation)
- Email: Optional (NO validation if provided)
- Phone: Optional (NO validation)
- Therapist ID: Must be valid UUID

**Missing:**
- ✗ Name length validation (min/max)
- ✗ Email format validation
- ✗ Phone format validation
- ✗ Therapist existence check
- ✗ Duplicate patient name check

### Frontend Validation

**Missing:**
- ✗ No patient creation form yet (not implemented)

---

## 4. Note Extraction & Session Status Validation

### Backend Validation (backend/app/models/schemas.py)

**ExtractedNotes Schema:**
```python
class ExtractedNotes(BaseModel):
    # Core content
    key_topics: List[str] = Field(..., description="Main subjects discussed (3-7 items)")
    topic_summary: str = Field(..., description="2-3 sentence overview")
    
    # Clinical data
    strategies: List[Strategy] = Field(default_factory=list)
    emotional_themes: List[str] = Field(default_factory=list)
    triggers: List[Trigger] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    
    # ... more fields
```

**Validation Present:**
- ✓ Field types enforced (Pydantic)
- ✓ Enum validation for mood, status fields
- ✓ Nested object validation

**Missing:**
- ✗ No length constraints on topics, summaries (Field descriptions not enforced)
- ✗ No validation on text content length
- ✗ Descriptions say "3-7 items" but no actual validation
- ✗ No risk flag severity validation (should be enum)
- ✗ descriptions in ExtractedNotes don't translate to validation

---

## 5. API Error Response Format

### Backend Error Response (FastAPI)
```python
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Email already registered"
)
```

**Response format:**
```json
{
  "detail": "Email already registered"
}
```

### Frontend Error Handling
```typescript
// api-client.ts line 37-38
const error = await response.json();
throw new Error(error.detail || 'API request failed');
```

**Issue:**
- ✓ Backend correctly uses `detail` field
- ✓ Frontend correctly reads `detail` field
- But original catch block in auth pages expects `message` field

---

## Recommendations

### Priority 1: Security & Consistency
1. **Standardize error handling**
   - Ensure all error responses use consistent format
   - Test error propagation from API to UI

2. **Add file size validation**
   ```python
   # In sessions.py upload_audio_session()
   if file.size and file.size > MAX_FILE_SIZE:
       raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE/1024/1024}MB")
   ```

3. **Add MIME type validation**
   ```python
   allowed_mimetypes = {
       'audio/mpeg', 'audio/wav', 'audio/mp4', 
       'audio/webm', 'audio/x-m4a'
   }
   if file.content_type not in allowed_mimetypes:
       raise HTTPException(400, f"Invalid audio format: {file.content_type}")
   ```

4. **Validate patient exists before session upload**
   ```python
   patient_result = await db.execute(
       select(db_models.Patient).where(db_models.Patient.id == patient_id)
   )
   if not patient_result.scalar_one_or_none():
       raise HTTPException(404, "Patient not found")
   ```

### Priority 2: Data Integrity
1. **Add string length constraints to patient data**
   ```python
   class PatientBase(BaseModel):
       name: str = Field(..., min_length=1, max_length=200)
       email: Optional[EmailStr] = None
       phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
   ```

2. **Enforce ExtractedNotes constraints**
   ```python
   key_topics: List[str] = Field(..., min_items=3, max_items=7)
   topic_summary: str = Field(..., min_length=10, max_length=500)
   ```

3. **Add password strength validation**
   ```python
   from pydantic import field_validator
   
   class UserCreate(BaseModel):
       password: str = Field(..., min_length=8)
       
       @field_validator('password')
       def validate_password_strength(cls, v):
           if not re.search(r'[A-Z]', v):
               raise ValueError('Password must contain uppercase letter')
           if not re.search(r'[a-z]', v):
               raise ValueError('Password must contain lowercase letter')
           if not re.search(r'[0-9]', v):
               raise ValueError('Password must contain digit')
           return v
   ```

### Priority 3: User Experience
1. **Add frontend file validation**
   ```typescript
   const handleFileSelect = (file: File) => {
       const allowed = ['audio/mpeg', 'audio/wav', 'audio/mp4'];
       if (!allowed.includes(file.type)) {
           setError(`Invalid file type. Allowed: ${allowed.join(', ')}`);
           return;
       }
       if (file.size > 100 * 1024 * 1024) {
           setError('File too large (max 100MB)');
           return;
       }
   }
   ```

2. **Add frontend password strength indicator**
   - Show requirements in signup form
   - Use color coding for strength

3. **Improve error messages for auth failures**
   - Distinguish between email not found vs wrong password (for security testing)
   - Display specific validation errors from backend

### Priority 4: Completeness
1. Create patient creation form with validation
2. Add form validation library (consider zod or react-hook-form)
3. Add comprehensive validation tests
4. Document validation rules in README

---

## Testing Checklist

- [ ] Signup with invalid email formats
- [ ] Signup with password < 8 characters  
- [ ] Signup with duplicate email
- [ ] Login with correct/incorrect credentials
- [ ] Upload file > 100MB
- [ ] Upload non-audio file (e.g., .txt renamed to .mp3)
- [ ] Upload without selecting file
- [ ] Create patient with empty name
- [ ] Create patient with invalid phone format
- [ ] Verify error messages match between client expectations and server responses

