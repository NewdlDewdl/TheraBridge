# Form Validation - Code Locations & Examples

## BACKEND VALIDATION IMPLEMENTATION

### 1. Authentication Validation (Pydantic Schemas)

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/auth/schemas.py`

```python
# Lines 11-16: User Registration Schema
class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr  # ✓ Auto-validates email format via pydantic-core
    password: str = Field(..., min_length=8)  # ✓ Minimum length check
    full_name: str = Field(..., min_length=1)  # ✓ Minimum length check
    role: UserRole  # ✓ Enum validation

# Lines 19-22: User Login Schema
class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr  # ✓ Email format validation
    password: str    # ✗ No length validation here (should have min_length=8)
```

**What's Missing:**
- Password strength rules (uppercase, lowercase, digits, special chars)
- Full name format validation (rejects whitespace-only strings)

---

### 2. Authentication Router (Business Logic)

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/auth/router.py`

```python
# Lines 27-87: Login Endpoint
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # ✓ Rate limiting
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    # Line 48: Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Lines 50-54: Check user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"  # ✓ Generic message (security best practice)
        )
    
    # Lines 57-61: Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Lines 64-68: Check account active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    # ... rest of token generation

# Lines 90-155: Signup Endpoint
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")  # ✓ Rate limiting against account spam
def signup(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    # Lines 111-116: Check email uniqueness
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Lines 119-125: Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    # Lines 127-136: Handle duplicates with IntegrityError
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
```

**Validation Summary:**
- ✓ Email uniqueness checked
- ✓ Email format validated (Pydantic EmailStr)
- ✓ Password minimum 8 chars enforced
- ✓ Rate limiting: 3/hour for signup, 5/minute for login
- ✗ No password strength rules
- ✗ No full name format validation

---

### 3. Session Upload Validation

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/sessions.py`

```python
# Line 28: File size constant (DEFINED BUT NEVER USED!)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Lines 118-210: Upload Audio Endpoint
@router.post("/upload", response_model=SessionResponse)
async def upload_audio_session(
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    # Lines 136-137: Check filename exists
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    # Lines 140-143: Check file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"File type {file_ext} not supported. Allowed: {allowed_extensions}")
    
    # ✗ MISSING: File size check (MAX_FILE_SIZE is defined on line 28 but NEVER CHECKED!)
    # ✗ MISSING: MIME type validation
    # ✗ MISSING: Patient existence validation
    # ✗ MISSING: Verify it's actually audio (could be .mp3 named text file)
    
    # Lines 146-151: Get therapist
    therapist_result = await db.execute(
        select(db_models.User).where(db_models.User.role == "therapist").limit(1)
    )
    therapist = therapist_result.scalar_one_or_none()
    if not therapist:
        raise HTTPException(500, "No therapist found in database")
    
    # Lines 156-162: Create session
    new_session = db_models.Session(
        patient_id=patient_id,  # ✗ NO VALIDATION THAT PATIENT EXISTS
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename=file.filename,
        status=SessionStatus.uploading.value
    )
```

**Critical Validation Gaps:**
1. File size check missing
2. MIME type validation missing
3. Patient existence not verified
4. File content not validated (only extension)

---

### 4. Patient Creation Validation

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/models/schemas.py`

```python
# Lines 173-177: Patient Base Schema
class PatientBase(BaseModel):
    """Base patient data"""
    name: str  # ✗ NO length validation (could be empty string after strip)
    email: Optional[str] = None  # ✗ NO format validation
    phone: Optional[str] = None  # ✗ NO format validation

# Lines 180-182: Patient Create Schema
class PatientCreate(PatientBase):
    """Request to create a new patient"""
    therapist_id: UUID  # ✓ UUID type enforced
```

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/routers/patients.py`

```python
# Lines 17-34: Create Patient Endpoint
@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,  # Pydantic validates schema
    db: AsyncSession = Depends(get_db)
):
    # ✗ No additional validation before creating patient
    new_patient = db_models.Patient(
        name=patient.name,  # ✗ Could be whitespace only
        email=patient.email,  # ✗ No format check if provided
        phone=patient.phone,  # ✗ No format check if provided
        therapist_id=patient.therapist_id
    )
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    
    return PatientResponse.model_validate(new_patient)
```

**Validation Gaps:**
- No name length constraints (min/max)
- No email format validation
- No phone format validation
- No duplicate name checking
- No therapist existence verification

---

### 5. Extracted Notes Validation (Schema Only)

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/backend/app/models/schemas.py`

```python
# Lines 93-121: Extracted Notes Schema
class ExtractedNotes(BaseModel):
    """Complete set of AI-extracted notes from a session"""

    # Lines 97-98: These have descriptions but NO Field constraints
    key_topics: List[str] = Field(..., description="Main subjects discussed (3-7 items)")
    # ✗ Description says "3-7 items" but no min_items=3, max_items=7
    
    topic_summary: str = Field(..., description="2-3 sentence overview")
    # ✗ Description says "2-3 sentence" but no length constraint
    
    # Lines 101-104: Lists with defaults
    strategies: List[Strategy] = Field(default_factory=list)
    emotional_themes: List[str] = Field(default_factory=list)
    triggers: List[Trigger] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    
    # Lines 107-108: Good enum usage
    session_mood: MoodLevel  # ✓ Enum enforced
    mood_trajectory: str = Field(..., description="improving, declining, stable, or fluctuating")
    # ✗ Should be enum, not str
    
    # Lines 116: Risk flags
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    # ✗ RiskFlag.severity is str, should be enum
    
    # Lines 119-120: Text fields with no length constraints
    therapist_notes: str = Field(..., description="Clinical summary for therapist (150-200 words)")
    # ✗ No length constraint
    
    patient_summary: str = Field(..., description="Friendly summary for patient (100-150 words)")
    # ✗ No length constraint
```

**Issue:** Descriptions document constraints but they're NOT enforced by Pydantic

---

## FRONTEND VALIDATION IMPLEMENTATION

### 1. Signup Form

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/app/auth/signup/page.tsx`

```typescript
// Lines 28-53: Form submission with minimal validation
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');

  // ✓ Password length check
  if (password.length < 8) {
    setError('Password must be at least 8 characters');
    return;
  }

  // ✗ No email format validation in JavaScript (relying on browser)
  // ✗ No full name validation
  // ✓ Role is safe (dropdown with fixed options)

  setIsLoading(true);

  try {
    await signup(email, password, fullName, role);  // Call auth context

    // Redirect based on role
    if (role === 'therapist') {
      router.push('/therapist');
    } else {
      router.push('/patient');
    }
  } catch (err: any) {
    setError(err.message || 'Signup failed');  // Error handling
  } finally {
    setIsLoading(false);
  }
};

// Lines 65-102: Form inputs
<Input
  id="fullName"
  type="text"
  value={fullName}
  onChange={(e) => setFullName(e.target.value)}
  required  // ✗ No length validation, just required
  placeholder="John Doe"
/>

<Input
  id="email"
  type="email"  // ✓ Browser native validation only
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  required
  placeholder="you@example.com"
/>

<Input
  id="password"
  type="password"
  value={password}
  onChange={(e) => setPassword(e.target.value)}
  required
  minLength={8}  // ✓ HTML5 constraint (but JavaScript also checks)
  placeholder="••••••••"
/>
```

**Validation Coverage:**
- ✓ Password min 8 (JavaScript check on line 32)
- ✓ Password minLength attribute (HTML5)
- ✓ Email type="email" (browser validation)
- ✗ Email format not validated in JavaScript
- ✗ Full name has no validation
- ✓ Role is safe dropdown

---

### 2. Login Form

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/app/auth/login/page.tsx`

```typescript
// Lines 33-45: Form submission with NO validation
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');
  setIsLoading(true);

  try {
    // ✗ NO VALIDATION before calling API
    // Just directly calls login with form values
    await login(email, password);
    setShouldRedirect(true);
  } catch (err: any) {
    // ✗ Error shows whatever err.message is
    // err might be a string, not an Error object
    setError(err.message || 'Login failed');
    setIsLoading(false);
  }
};

// Lines 57-79: Form inputs
<Input
  id="email"
  type="email"  // Browser native validation only
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  required
  placeholder="you@example.com"
/>

<Input
  id="password"
  type="password"
  value={password}
  onChange={(e) => setPassword(e.target.value)}
  required  // ✗ No minLength attribute!
  placeholder="••••••••"
/>
```

**Validation Coverage:**
- ✗ No password length check
- ✗ No email validation
- ✗ No validation before API call

**Issue:** Inconsistent with signup form which checks password length

---

### 3. API Client Error Handling

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/lib/api-client.ts`

```typescript
// Lines 13-45: Request method
async request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // ... setup code ...

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    // Lines 32-34: Handle 401 (token expired)
    if (response.status === 401) {
      return await this.handleTokenRefresh(endpoint, options);
    }

    // Lines 36-39: Handle error responses
    if (!response.ok) {
      const error = await response.json();
      // ✓ Correctly reads 'detail' field from error response
      throw new Error(error.detail || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
}
```

**Note:** This error handling is CORRECT - it properly reads `error.detail` which is what the backend returns.

---

### 4. Auth Context

**File:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/lib/auth-context.tsx`

```typescript
// Lines 54-62: Login method
const login = async (email: string, password: string) => {
  // ✗ No validation
  const response = await apiClient.post<{
    access_token: string;
    refresh_token: string;
  }>('/auth/login', { email, password });

  tokenStorage.saveTokens(response.access_token, response.refresh_token);
  await checkAuth();
};

// Lines 64-77: Signup method
const signup = async (email: string, password: string, fullName: string, role: string) => {
  // ✗ No validation here either
  const response = await apiClient.post<{
    access_token: string;
    refresh_token: string;
  }>('/auth/signup', {
    email,
    password,
    full_name: fullName,
    role,
  });

  tokenStorage.saveTokens(response.access_token, response.refresh_token);
  await checkAuth();
};
```

**Note:** Auth context just passes data to API - validation happens in page components and backend.

---

## VALIDATION FLOW DIAGRAM

```
SIGNUP FORM
===========

User Input
    |
    v
Frontend (signup/page.tsx):
  - Check password.length >= 8 ✓
  - Email type="email" (browser native) ✓
  - Full name required only ✗
    |
    v
Auth Context (lib/auth-context.tsx):
  - No validation, just forwards data ✓
    |
    v
API Client (lib/api-client.ts):
  - Reads error.detail on failure ✓
    |
    v
Backend (app/auth/router.py):
  - Check email format (EmailStr) ✓
  - Check password >= 8 chars ✓
  - Check full_name >= 1 char ✓
  - Check role is enum ✓
  - Check email unique ✓
  - Rate limit 3/hour ✓
  - Password strength ✗
  - Full name format ✗
    |
    v
Response: Success or HTTPException


LOGIN FORM
==========

User Input
    |
    v
Frontend (login/page.tsx):
  - No validation ✗
    |
    v
Auth Context:
  - No validation ✓ (expected)
    |
    v
API Client:
  - Reads error.detail ✓
    |
    v
Backend:
  - Check email format (EmailStr) ✓
  - Find user by email ✓
  - Verify password hash ✓
  - Check is_active ✓
  - Rate limit 5/minute ✓
  - Password strength ✗ (no strength to verify)
    |
    v
Response: Tokens or HTTPException(401)


SESSION UPLOAD
==============

User Input (file)
    |
    v
Frontend:
  - No validation ✗
    |
    v
Backend (app/routers/sessions.py):
  - Check filename exists ✓
  - Check extension in allowed list ✓
  - Size constant defined (MAX_FILE_SIZE) ✓
  - Check size against MAX ✗ (NOT IMPLEMENTED)
  - Check MIME type ✗
  - Check patient exists ✗
  - Check file is actually audio ✗
    |
    v
Response: Session created or HTTPException(400)


PATIENT CREATION
================

User Input
    |
    v
Frontend:
  - No form exists yet ✗
    |
    v
Backend (app/routers/patients.py):
  - Check schema (Pydantic validates)
  - Name validation ✗
  - Email validation ✗
  - Phone validation ✗
  - Therapist existence ✗
    |
    v
Response: Patient created or validation error
```

---

## ERROR RESPONSE EXAMPLES

### Successful Login
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Failed Login - Wrong Password
```json
{
  "detail": "Incorrect email or password"
}
```

### Failed Signup - Email Exists
```json
{
  "detail": "Email already registered"
}
```

### Failed Upload - Invalid Extension
```json
{
  "detail": "File type .txt not supported. Allowed: {'.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm'}"
}
```

### Pydantic Validation Error (Invalid Email)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "input": "not-an-email"
    }
  ]
}
```

---

## SUMMARY OF VALIDATION GAPS

| Feature | Frontend | Backend | Risk Level |
|---------|----------|---------|-----------|
| Email validation | Browser only | EmailStr ✓ | MINOR |
| Password strength | None | None | CRITICAL |
| File size | None | Constant defined but not checked | CRITICAL |
| File MIME type | None | None | CRITICAL |
| Patient existence | None | None | HIGH |
| Full name format | None | min_length=1 only | MEDIUM |
| Patient name | None | No validation | HIGH |
| Patient email format | None | None | MEDIUM |
| Patient phone format | None | None | MEDIUM |
| Rate limiting | None | Implemented ✓ | N/A |

