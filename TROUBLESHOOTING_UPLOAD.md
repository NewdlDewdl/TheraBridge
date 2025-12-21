# Upload Error Troubleshooting

**Error:** "Failed to upload file"

This error means the file can't be uploaded to Supabase Storage. Here are the fixes in order of likelihood:

---

## Fix 1: Check if Storage Bucket Exists (MOST LIKELY)

The `audio-sessions` storage bucket might not have been created.

### Check in Supabase:

1. Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/storage/buckets
2. Look for a bucket named `audio-sessions`

### If it doesn't exist, create it manually:

1. Click "New bucket"
2. Name: `audio-sessions`
3. **Public bucket:** NO (keep it private)
4. Click "Create bucket"

### Set bucket permissions:

1. Click on the `audio-sessions` bucket
2. Go to "Policies" tab
3. Click "New Policy"
4. **For INSERT (upload):**
   - Policy name: `Allow authenticated uploads`
   - Target roles: `authenticated`
   - Policy definition:
     ```sql
     true
     ```
   - Click "Review" → "Save policy"

5. **For SELECT (read):**
   - Click "New Policy"
   - Policy name: `Allow authenticated reads`
   - Target roles: `authenticated`
   - Policy definition:
     ```sql
     true
     ```
   - Click "Review" → "Save policy"

---

## Fix 2: Disable Row Level Security (TEMPORARY - for testing)

The RLS policies might be blocking the upload.

Run this SQL in Supabase SQL Editor:

```sql
-- Temporarily disable RLS for testing
ALTER TABLE therapy_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE patients DISABLE ROW LEVEL SECURITY;
```

**⚠️ WARNING:** This makes your data publicly accessible. Only use for testing, then re-enable:

```sql
-- Re-enable RLS when done testing
ALTER TABLE therapy_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

---

## Fix 3: Verify Test Users Exist

Make sure the test users were created:

Run this SQL:

```sql
SELECT * FROM users WHERE id IN (
  '00000000-0000-0000-0000-000000000001'::uuid,
  '00000000-0000-0000-0000-000000000002'::uuid
);

SELECT * FROM patients WHERE id = '00000000-0000-0000-0000-000000000003'::uuid;
```

**Expected result:**
- 2 users (therapist + patient)
- 1 patient record

**If empty**, re-run `/supabase/test-data.sql`

---

## Fix 4: Check Browser Console for Detailed Error

The error message should now show more details.

1. Open browser DevTools (F12 or right-click → Inspect)
2. Go to "Console" tab
3. Try uploading again
4. Look for error messages - they should now say:
   - `Failed to upload file: [specific error]`
   - `Failed to create session record: [specific error]`

**Common errors and fixes:**

### "Bucket not found"
→ Go to Fix 1 above (create storage bucket)

### "new row violates row-level security policy"
→ Go to Fix 2 above (disable RLS temporarily)

### "null value in column 'patient_id' violates not-null constraint"
→ Go to Fix 3 above (create test users)

### "permission denied for table"
→ Your Supabase anon key doesn't have permissions. Check `.env.local` has correct key.

---

## Fix 5: Verify Environment Variables

Check that `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/.env.local` has:

```env
NEXT_PUBLIC_SUPABASE_URL=https://rfckpldoohyjctrqxmiv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmY2twbGRvb2h5amN0cnF4bWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ4MzI0OTIsImV4cCI6MjA1MDQwODQ5Mn0.gIaGWkU_tL0MlZRvRMnDCqHE7vx6ydyxWLrH8wXLG_4
OPENAI_API_KEY=sk-proj-...
```

**After changing `.env.local`:**
1. Stop the dev server (Ctrl+C)
2. Restart: `npm run dev`
3. Try uploading again

---

## Quick Test Sequence

**Do these in order:**

1. ✅ **Create storage bucket** (Fix 1) - 1 minute
2. ✅ **Disable RLS temporarily** (Fix 2) - 30 seconds
3. ✅ **Verify test users** (Fix 3) - 30 seconds
4. ✅ **Try uploading** - Should work now!
5. ✅ **Check browser console** if still failing

---

## After It Works

Once upload works, you can re-enable security:

1. **Re-enable RLS:**
   ```sql
   ALTER TABLE therapy_sessions ENABLE ROW LEVEL SECURITY;
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
   ```

2. **Set proper RLS policies** (for production):
   ```sql
   -- Allow users to insert their own sessions
   CREATE POLICY "Users can insert own sessions" ON therapy_sessions
     FOR INSERT WITH CHECK (auth.uid() = therapist_id);

   -- Allow users to read their own sessions
   CREATE POLICY "Users can read own sessions" ON therapy_sessions
     FOR SELECT USING (
       auth.uid() = therapist_id OR
       auth.uid() IN (SELECT user_id FROM patients WHERE id = patient_id)
     );
   ```

---

## Still Not Working?

**Share the exact error message from the browser console** and I'll help debug further.

The error should now say something like:
- `Failed to upload file: [reason]`
- `Failed to create session record: [reason]`

This will tell us exactly what's wrong!
