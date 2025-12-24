# Hackathon Demo Mode - Setup Guide

## 🎯 Implementation Complete!

All 5 phases of the Hackathon Demo Mode have been successfully implemented. This guide will help you deploy and test the demo mode.

---

## ✅ What's Been Implemented

### Phase 1: Database Schema ✅
- Migration to add demo user fields (demo_token, is_demo, demo_created_at, demo_expires_at)
- SQL function to seed 10 fully-analyzed therapy sessions
- Auto-cleanup function for expired demos (24h)

### Phase 2: Backend API ✅
- Demo authentication middleware
- `/api/demo/initialize` - Creates new demo user
- `/api/demo/reset` - Resets to fresh 10 sessions
- `/api/demo/status` - Check demo status
- `/api/sessions/upload-demo-transcript` - Upload demo sessions

### Phase 3: Frontend Token Management ✅
- localStorage wrapper for demo tokens
- Demo API client
- Automatic token injection in all API requests

### Phase 4: UI Components ✅
- "Reset Demo" button in NavigationBar with confirmation modal
- Demo transcript uploader in upload page
- Dropdown to select from 2 demo sessions

### Phase 5: Dashboard Integration ✅
- Auto-initialization on first visit
- Loading states during demo setup
- Real-time updates via ProcessingContext
- Fetches real session data from backend

---

## 🚀 Deployment Steps

### Step 1: Apply Database Migrations

1. Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql

2. Click "New Query" and execute each migration in order:

**Migration 1: Schema Changes**
```sql
-- Copy contents of backend/supabase/migrations/007_add_demo_mode_support.sql
-- Adds demo_token, is_demo, demo_created_at, demo_expires_at to users table
```

**Migration 2: Seed Function**
```sql
-- Copy contents of backend/supabase/seed_demo_data.sql
-- Creates the seed_demo_user_sessions() function
```

**Migration 3: Cleanup Function**
```sql
-- Copy contents of backend/supabase/cleanup_demo_data.sql
-- Creates the cleanup_expired_demo_users() function
```

3. Test the seed function:
```sql
SELECT * FROM seed_demo_user_sessions(gen_random_uuid());
```

4. Verify the schema:
```sql
\d users  -- should show new demo columns
```

### Step 2: Start Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/health
```

### Step 3: Start Frontend Server

```bash
cd frontend
npm run dev
```

Frontend will run on: http://localhost:3000

---

## 🧪 Testing the Demo Flow

### Test 1: First Visit - Auto Initialization
1. Open **incognito window**
2. Navigate to http://localhost:3000/dashboard
3. **Expected:**
   - See "Initializing demo..." spinner (brief)
   - Dashboard loads with 10 sessions
   - localStorage should have `therapybridge_demo_token`

### Test 2: Demo Transcript Upload
1. Navigate to http://localhost:3000/upload
2. Select "Session 12: Thriving" from dropdown
3. Click "Upload & Analyze"
4. **Expected:**
   - Processing screen appears
   - Progress updates every 2 seconds
   - After ~10 seconds, shows completion
   - Dashboard auto-refreshes with 11 sessions

### Test 3: Reset Demo
1. Click "Reset Demo" button in top right of navbar
2. Confirm in modal
3. **Expected:**
   - Page reloads
   - Back to original 10 sessions
   - Uploaded session is gone

### Test 4: Token Persistence
1. Upload a demo session (so you have 11 sessions)
2. Close browser completely
3. Reopen and navigate to dashboard
4. **Expected:**
   - Same 11 sessions still present
   - No re-initialization

### Test 5: Token Expiry (Manual Test)
1. In Supabase SQL Editor:
```sql
UPDATE users
SET demo_expires_at = NOW() - INTERVAL '1 hour'
WHERE is_demo = TRUE
LIMIT 1;
```
2. Refresh dashboard
3. **Expected:**
   - New demo initializes
   - Fresh 10 sessions

---

## 📊 Demo Sessions Included

The seed function creates 10 therapy sessions with full AI analysis:

1. **Session 1** - Crisis Intake (2025-01-10) - Breakthrough ⭐
2. **Session 2** - Emotional Regulation (2025-01-13)
3. **Session 3** - ADHD Discovery (2025-01-20) - Breakthrough ⭐
4. **Session 4** - Medication Start (2025-01-27)
5. **Session 5** - Family Conflict (2025-02-03)
6. **Session 6** - Spring Break Hope (2025-02-17)
7. **Session 7** - Dating Anxiety (2025-03-03)
8. **Session 8** - Relationship Boundaries (2025-03-10)
9. **Session 9** - Coming Out Preparation (2025-03-24)
10. **Session 10** - Coming Out Aftermath (2025-03-31) - Breakthrough ⭐

Each session includes:
- Mood score (0.0-10.0) with confidence
- Topics and action items
- Therapy technique used
- Summary
- Breakthrough detection (3 sessions have breakthroughs)

---

## 🔧 API Endpoints

### Demo Management
- `POST /api/demo/initialize` - Create new demo user
- `POST /api/demo/reset` - Reset to fresh sessions (requires X-Demo-Token header)
- `GET /api/demo/status` - Get demo status (requires X-Demo-Token header)

### Session Management
- `POST /api/sessions/upload-demo-transcript?session_file=session_12_thriving.json` - Upload demo transcript
- `GET /api/sessions/patient/{patient_id}` - Get all sessions for patient
- `GET /api/sessions/{session_id}/status` - Get processing status

### Testing with cURL

**Initialize Demo:**
```bash
curl -X POST http://localhost:8000/api/demo/initialize | jq
```

**Get Status:**
```bash
TOKEN="your-demo-token-here"
curl -H "X-Demo-Token: $TOKEN" http://localhost:8000/api/demo/status | jq
```

**Upload Demo Transcript:**
```bash
curl -X POST \
  -H "X-Demo-Token: $TOKEN" \
  "http://localhost:8000/api/sessions/upload-demo-transcript?session_file=session_12_thriving.json" | jq
```

**Reset Demo:**
```bash
curl -X POST \
  -H "X-Demo-Token: $TOKEN" \
  http://localhost:8000/api/demo/reset | jq
```

---

## 🗂️ Files Created/Modified

### Backend Files
```
backend/
├── supabase/
│   ├── migrations/007_add_demo_mode_support.sql (NEW)
│   ├── seed_demo_data.sql (NEW)
│   └── cleanup_demo_data.sql (NEW)
├── app/
│   ├── middleware/
│   │   └── demo_auth.py (NEW)
│   ├── routers/
│   │   ├── demo.py (NEW)
│   │   └── sessions.py (MODIFIED - added upload-demo-transcript)
│   └── main.py (MODIFIED - registered demo router)
└── apply_demo_migrations.py (NEW)
```

### Frontend Files
```
frontend/
├── lib/
│   ├── demo-token-storage.ts (NEW)
│   ├── demo-api-client.ts (NEW)
│   └── api-client.ts (MODIFIED - added X-Demo-Token header)
├── hooks/
│   └── useDemoInitialization.ts (NEW)
├── components/
│   └── NavigationBar.tsx (MODIFIED - added Reset Demo button)
├── app/
│   ├── dashboard/
│   │   └── page.tsx (MODIFIED - added demo initialization)
│   ├── upload/
│   │   ├── page.tsx (MODIFIED - added demo uploader)
│   │   └── components/
│   │       └── DemoTranscriptUploader.tsx (NEW)
│   └── patient/
│       └── lib/
│           └── usePatientSessions.ts (MODIFIED - fetch real data)
```

---

## 🔍 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Supabase connection
python -c "from app.database import get_supabase; db = get_supabase(); print('✓ Connected')"
```

### Frontend build fails
```bash
# Clear build cache
rm -rf .next node_modules
npm install
npm run build
```

### Demo initialization fails
1. Check browser console for errors
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check Network tab for API calls
4. Verify Supabase migrations applied: `SELECT * FROM users WHERE is_demo = TRUE LIMIT 1;`

### Sessions not loading
1. Check localStorage has token: `localStorage.getItem('therapybridge_demo_token')`
2. Verify patient_id: `localStorage.getItem('therapybridge_demo_patient_id')`
3. Check API response: `GET /api/sessions/patient/{patient_id}`

---

## 📝 Environment Variables

### Backend `.env`
```bash
SUPABASE_URL=https://rfckpldoohyjctrqxmiv.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎉 Success Checklist

- [ ] Database migrations applied successfully
- [ ] Backend server starts without errors
- [ ] Frontend builds and starts successfully
- [ ] Demo initializes automatically on dashboard load
- [ ] 10 sessions appear on dashboard
- [ ] Can upload demo transcript
- [ ] AI analysis runs (~10 seconds)
- [ ] Dashboard auto-refreshes with new session
- [ ] Reset Demo button works
- [ ] Token persists across browser sessions
- [ ] Expired tokens trigger new demo initialization

---

## 📚 Additional Resources

- **Implementation Plan:** `Project MDs/plans/2025-12-23-hackathon-demo-mode.md`
- **Supabase Dashboard:** https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv
- **Backend API Docs:** http://localhost:8000/docs (when server is running)

---

## 🚨 Important Notes

1. **Demo tokens are NOT encrypted** - This is for demo purposes only
2. **24h auto-cleanup** - Data automatically deletes after 24 hours
3. **No real authentication** - Demo mode bypasses standard auth
4. **Local storage only** - Tokens stored in browser localStorage
5. **Real AI analysis** - Demo uploads trigger actual OpenAI API calls (~$0.01 per session)

---

## 🎯 Next Steps

1. Apply database migrations via Supabase SQL Editor
2. Test the complete flow locally
3. Deploy backend to Railway/Heroku
4. Deploy frontend to Vercel/Netlify
5. Update frontend API URL to production backend
6. Test production deployment end-to-end

**Ready for hackathon presentation!** 🚀
