# TherapyBridge Backend - Complete Testing Guide

This guide will walk you through testing the entire pipeline from audio upload through AI extraction.

## Prerequisites

- Backend server running on port 8000
- Audio file for testing (MP3, WAV, or M4A format)
- `curl` and `jq` installed (or use the interactive API docs)

## Quick Setup

```bash
# Start the server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# In a new terminal, verify server is running
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "transcription": "available",
    "extraction": "available"
  }
}
```

---

## Testing Workflow

### Phase 1: Verify Infrastructure

#### Test 1.1: Health Check
```bash
curl http://localhost:8000/health | jq
```

✅ **Expected**: Status 200, all services "available"

#### Test 1.2: API Documentation
```bash
# Open in browser
open http://localhost:8000/docs
```

✅ **Expected**: Interactive Swagger UI with all endpoints listed

#### Test 1.3: Database Connection
```bash
curl http://localhost:8000/api/patients/ | jq
```

✅ **Expected**: Array with seeded "Test Patient"

---

### Phase 2: Patient Management

#### Test 2.1: List Patients
```bash
curl http://localhost:8000/api/patients/ | jq
```

✅ **Expected**: JSON array with patient objects including `id`, `name`, `therapist_id`

**Save the patient ID** from the response for the next steps:
```bash
export PATIENT_ID="<paste-uuid-here>"
echo "Patient ID: $PATIENT_ID"
```

#### Test 2.2: Get Specific Patient
```bash
curl "http://localhost:8000/api/patients/$PATIENT_ID" | jq
```

✅ **Expected**: Single patient object with full details

#### Test 2.3: Create New Patient (Optional)
```bash
# First, get therapist ID
export THERAPIST_ID=$(curl -s http://localhost:8000/api/patients/ | jq -r '.[0].therapist_id')

# Create new patient
curl -X POST http://localhost:8000/api/patients/ \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Jane Doe\",
    \"email\": \"jane@example.com\",
    \"phone\": \"555-1234\",
    \"therapist_id\": \"$THERAPIST_ID\"
  }" | jq
```

✅ **Expected**: New patient object with generated UUID

---

### Phase 3: Audio Upload & Processing Pipeline

#### Test 3.1: Prepare Test Audio

**Option A: Use existing test file**
```bash
# From audio-transcription-pipeline
export AUDIO_FILE="../audio-transcription-pipeline/tests/samples/onemintestvid.mp3"

# Verify file exists
ls -lh "$AUDIO_FILE"
```

**Option B: Use your own audio**
```bash
export AUDIO_FILE="/path/to/your/audio.mp3"
```

#### Test 3.2: Upload Audio Session
```bash
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@$AUDIO_FILE" | jq > session_response.json

# Extract session ID
export SESSION_ID=$(jq -r '.id' session_response.json)
echo "Session ID: $SESSION_ID"
echo "Initial Status: $(jq -r '.status' session_response.json)"
```

✅ **Expected**:
- Status 200
- Response includes `id`, `status: "uploading"`, `patient_id`, `audio_filename`

#### Test 3.3: Monitor Processing Status

The session processes in background through these stages:
1. `uploading` → `transcribing` → `transcribed` → `extracting_notes` → `processed`

**Poll the session endpoint** to watch progress:

```bash
# Check status every 10 seconds
watch -n 10 "curl -s http://localhost:8000/api/sessions/$SESSION_ID | jq '.status'"
```

Or use this loop:
```bash
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq -r '.status')
  echo "$(date '+%H:%M:%S') - Status: $STATUS"

  if [ "$STATUS" == "processed" ]; then
    echo "✅ Processing complete!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "❌ Processing failed!"
    curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.error_message'
    break
  fi

  sleep 10
done
```

✅ **Expected**: Status progresses to `processed` (may take 2-5 minutes for short audio)

**Typical Timeline:**
- 1-min audio: ~1-2 minutes total
- 5-min audio: ~2-3 minutes total
- 30-min audio: ~5-8 minutes total

---

### Phase 4: Verify Extracted Data

#### Test 4.1: Get Complete Session Data
```bash
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq > session_complete.json

# View key fields
cat session_complete.json | jq '{
  id,
  status,
  duration_seconds,
  session_mood: .extracted_notes.session_mood,
  topics: .extracted_notes.key_topics,
  strategies_count: (.extracted_notes.strategies | length),
  action_items_count: (.extracted_notes.action_items | length)
}'
```

✅ **Expected**: Full session object with:
- `status: "processed"`
- `transcript_text` populated
- `extracted_notes` object with all fields

#### Test 4.2: Get Extracted Notes Only
```bash
curl "http://localhost:8000/api/sessions/$SESSION_ID/notes" | jq > notes.json

# View notes summary
cat notes.json | jq '{
  topics: .key_topics,
  summary: .topic_summary,
  mood: .session_mood,
  mood_trajectory: .mood_trajectory,
  strategies_count: (.strategies | length),
  triggers_count: (.triggers | length),
  action_items_count: (.action_items | length),
  risk_flags_count: (.risk_flags | length)
}'
```

✅ **Expected**: Structured notes with:
- 3-7 key topics
- Topic summary (2-3 sentences)
- Session mood (very_low, low, neutral, positive, or very_positive)
- Mood trajectory (improving, declining, stable, or fluctuating)
- Arrays of strategies, triggers, action items
- Risk flags array (may be empty if no concerns)

#### Test 4.3: Review AI-Generated Summaries
```bash
# Therapist summary
echo "=== THERAPIST SUMMARY ==="
cat notes.json | jq -r '.therapist_notes'

echo -e "\n=== PATIENT SUMMARY ==="
cat notes.json | jq -r '.patient_summary'
```

✅ **Expected**:
- Therapist summary: 150-200 words, clinical tone
- Patient summary: 100-150 words, warm/supportive tone

#### Test 4.4: Examine Detailed Extractions
```bash
# View all strategies
echo "=== STRATEGIES ==="
cat notes.json | jq '.strategies[] | {name, category, status, context}'

# View all action items
echo -e "\n=== ACTION ITEMS ==="
cat notes.json | jq '.action_items[] | {task, category, details}'

# View triggers
echo -e "\n=== TRIGGERS ==="
cat notes.json | jq '.triggers[] | {trigger, severity, context}'

# Check for risk flags
echo -e "\n=== RISK FLAGS ==="
cat notes.json | jq '.risk_flags[]'
```

✅ **Expected**: Arrays populated with extracted data from transcript

---

### Phase 5: Session Management

#### Test 5.1: List All Sessions
```bash
curl http://localhost:8000/api/sessions/ | jq 'map({id, status, patient_id, session_date})'
```

✅ **Expected**: Array of all sessions, sorted by most recent first

#### Test 5.2: Filter Sessions by Patient
```bash
curl "http://localhost:8000/api/sessions/?patient_id=$PATIENT_ID" | jq
```

✅ **Expected**: Only sessions for the specified patient

#### Test 5.3: Filter Sessions by Status
```bash
curl "http://localhost:8000/api/sessions/?status=processed" | jq
```

✅ **Expected**: Only sessions with `status: "processed"`

#### Test 5.4: Manual Re-extraction (Optional)
```bash
# Force re-extraction of notes (useful if you update the prompt)
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/extract-notes" | jq
```

✅ **Expected**: New extracted notes with `processing_time` metric

---

### Phase 6: Edge Cases & Error Handling

#### Test 6.1: Invalid Patient ID
```bash
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=invalid-uuid" \
  -F "file=@$AUDIO_FILE"
```

✅ **Expected**: Status 422 (Validation Error)

#### Test 6.2: Missing File
```bash
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID"
```

✅ **Expected**: Status 422 (Missing required field)

#### Test 6.3: Unsupported File Type
```bash
# Create a fake text file
echo "test" > test.txt
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@test.txt"
rm test.txt
```

✅ **Expected**: Status 400 (File type not supported)

#### Test 6.4: Nonexistent Session
```bash
curl "http://localhost:8000/api/sessions/00000000-0000-0000-0000-000000000000"
```

✅ **Expected**: Status 404 (Session not found)

#### Test 6.5: Get Notes Before Processing Complete
```bash
# Try to get notes for a session still processing
# (Upload a new session and immediately try to get notes)
NEW_SESSION=$(curl -s -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@$AUDIO_FILE" | jq -r '.id')

curl "http://localhost:8000/api/sessions/$NEW_SESSION/notes"
```

✅ **Expected**: Status 404 (Notes not yet extracted)

---

### Phase 7: Performance & Quality Validation

#### Test 7.1: Extraction Quality Check

**Manual Review Checklist:**

```bash
# Display the full notes for human review
cat notes.json | jq
```

Verify:
- [ ] Key topics accurately reflect transcript content
- [ ] Topic summary is coherent and accurate
- [ ] Strategies are correctly categorized (breathing, cognitive, behavioral, etc.)
- [ ] Action items are specific and actionable
- [ ] Mood assessment seems appropriate
- [ ] Therapist summary is professional and clinical
- [ ] Patient summary is warm and encouraging
- [ ] No hallucinated information (check against transcript)
- [ ] Risk flags are appropriate (not over-flagged or under-flagged)

#### Test 7.2: Cost Estimation
```bash
# Run unit test for cost estimation
cd backend
pytest tests/test_extraction_service.py::test_cost_estimation -v -s
```

✅ **Expected**: Estimated cost < $0.05 per session

#### Test 7.3: Processing Time Measurement
```bash
# Re-extract with timing
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/extract-notes" | jq '.processing_time'
```

✅ **Expected**: ~15-30 seconds for typical session

---

### Phase 8: Database Verification (Optional)

#### Test 8.1: Direct Database Query
```bash
# Load database URL
source ../audio-transcription-pipeline/.env

# Query sessions table
psql "$DATABASE_URL" -c "
  SELECT id, status, audio_filename,
         LENGTH(transcript_text) as transcript_length,
         extracted_notes IS NOT NULL as has_notes
  FROM sessions
  ORDER BY created_at DESC
  LIMIT 5;
"
```

✅ **Expected**: Sessions with transcript and notes data

#### Test 8.2: Verify Relationships
```bash
psql "$DATABASE_URL" -c "
  SELECT
    s.id as session_id,
    p.name as patient_name,
    u.name as therapist_name,
    s.status
  FROM sessions s
  JOIN patients p ON s.patient_id = p.id
  JOIN users u ON s.therapist_id = u.id
  ORDER BY s.created_at DESC
  LIMIT 5;
"
```

✅ **Expected**: Proper joins showing relationships

---

## Interactive API Testing (Alternative)

Instead of curl commands, use the built-in Swagger UI:

1. Open http://localhost:8000/docs
2. Click on an endpoint to expand it
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. Review response

**Recommended flow:**
1. GET `/api/patients/` → Get patient ID
2. POST `/api/sessions/upload` → Upload audio with patient ID
3. GET `/api/sessions/{id}` → Monitor status (refresh until "processed")
4. GET `/api/sessions/{id}/notes` → View extracted notes

---

## Automated Test Suite

Run the complete unit test suite:

```bash
cd backend
pytest tests/test_extraction_service.py -v -s
```

✅ **Expected**: All tests passing

**Sample output:**
```
tests/test_extraction_service.py::test_extract_notes_basic PASSED
tests/test_extraction_service.py::test_cost_estimation PASSED

============================================================
EXTRACTED NOTES
============================================================

Topics: work stress, sleep disruption, self-judgment, ...
Mood: neutral (improving)
Strategies: 3 extracted
Action Items: 2 extracted
```

---

## Troubleshooting

### Server not responding
```bash
# Check if server is running
lsof -i :8000

# View server logs
# (Check terminal where uvicorn is running)
```

### Upload fails
```bash
# Verify file exists and is readable
ls -lh "$AUDIO_FILE"
file "$AUDIO_FILE"

# Check file size (max 100MB)
du -h "$AUDIO_FILE"

# Verify patient ID is valid UUID
echo "$PATIENT_ID" | grep -E '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
```

### Processing stuck
```bash
# Check session error message
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.error_message'

# Check server logs for errors

# Verify OpenAI API key is set
grep OPENAI_API_KEY ../audio-transcription-pipeline/.env
```

### Empty extracted notes
```bash
# Verify transcript exists
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.transcript_text' | head -20

# Try manual re-extraction
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/extract-notes" | jq
```

---

## Success Criteria

Your backend is working correctly if:

- ✅ Health check returns healthy status
- ✅ Can list patients from database
- ✅ Can upload audio file successfully
- ✅ Session progresses through all statuses (uploading → transcribing → transcribed → extracting_notes → processed)
- ✅ Transcript is populated with text
- ✅ Extracted notes contain all expected fields
- ✅ Therapist and patient summaries are generated
- ✅ AI extraction completes in reasonable time (~20-30 seconds)
- ✅ No errors in server logs
- ✅ Can retrieve session and notes via API

---

## Next Steps

Once all tests pass:

1. **Test with real therapy audio** - Use an actual session recording
2. **Validate extraction quality** - Review notes for accuracy
3. **Measure actual costs** - Check OpenAI usage dashboard
4. **Build frontend** - Create UI to interact with these endpoints
5. **Add authentication** - Secure the API endpoints
6. **Deploy to production** - Move from local to cloud hosting

---

## Quick Test Script

Save this as `test_pipeline.sh` for one-command testing:

```bash
#!/bin/bash
set -e

echo "🧪 Testing TherapyBridge Backend Pipeline"
echo "=========================================="

# 1. Health check
echo -e "\n✓ Testing health endpoint..."
curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null
echo "  Health check: PASSED"

# 2. Get patient ID
echo -e "\n✓ Getting patient ID..."
PATIENT_ID=$(curl -s http://localhost:8000/api/patients/ | jq -r '.[0].id')
echo "  Patient ID: $PATIENT_ID"

# 3. Upload audio
echo -e "\n✓ Uploading test audio..."
AUDIO_FILE="${1:-../audio-transcription-pipeline/tests/samples/onemintestvid.mp3}"
if [ ! -f "$AUDIO_FILE" ]; then
  echo "  ERROR: Audio file not found: $AUDIO_FILE"
  exit 1
fi

SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@$AUDIO_FILE" | jq -r '.id')
echo "  Session ID: $SESSION_ID"

# 4. Wait for processing
echo -e "\n✓ Waiting for processing to complete..."
MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq -r '.status')
  echo -n "  $(date '+%H:%M:%S') - Status: $STATUS"

  if [ "$STATUS" == "processed" ]; then
    echo " ✅"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo " ❌"
    curl -s "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.error_message'
    exit 1
  else
    echo ""
  fi

  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo "  ERROR: Processing timeout"
  exit 1
fi

# 5. Verify extracted notes
echo -e "\n✓ Verifying extracted notes..."
NOTES=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID/notes")
TOPICS=$(echo "$NOTES" | jq -r '.key_topics | length')
STRATEGIES=$(echo "$NOTES" | jq -r '.strategies | length')
echo "  Topics extracted: $TOPICS"
echo "  Strategies extracted: $STRATEGIES"

echo -e "\n🎉 All tests PASSED!"
echo "Session ID: $SESSION_ID"
echo "View full notes: curl http://localhost:8000/api/sessions/$SESSION_ID/notes | jq"
```

Usage:
```bash
chmod +x test_pipeline.sh
./test_pipeline.sh [/path/to/audio.mp3]
```

---

**Ready to test the complete pipeline!** Start with Phase 1 and work through each phase systematically.
