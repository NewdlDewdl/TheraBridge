# Test the TherapyBridge Backend Pipeline

Use this prompt to quickly test the complete audio → transcript → AI extraction pipeline.

## Quick Test (Automated)

```bash
cd backend

# Make sure server is running in another terminal:
# uvicorn app.main:app --reload

# Run the automated test script
./test_pipeline.sh

# Or test with your own audio file:
./test_pipeline.sh /path/to/your/audio.mp3
```

Expected output:
```
🧪 Testing TherapyBridge Backend Pipeline
==========================================

✓ Testing health endpoint...
  Health check: PASSED

✓ Getting patient ID...
  Patient ID: 9f2b1a1a-968a-4bf2-8013-4794ed63451e

✓ Uploading test audio...
  Session ID: abc123...

✓ Waiting for processing to complete...
  18:30:15 - Status: uploading
  18:30:25 - Status: transcribing
  18:30:35 - Status: transcribed
  18:30:45 - Status: extracting_notes
  18:30:55 - Status: processed ✅

✓ Verifying extracted notes...
  Topics extracted: 5
  Strategies extracted: 3
  Action items: 2
  Session mood: neutral

📊 EXTRACTION SUMMARY
====================
Topics: work stress, sleep disruption, self-judgment, ...
Summary: [AI-generated summary]
Mood: neutral (improving)

🎉 All tests PASSED!
```

---

## Manual Testing Steps

### 1. Start the Server
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Keep this terminal open - you'll see request logs here.

### 2. Test Health Check (New Terminal)
```bash
curl http://localhost:8000/health | jq
```

Should return: `"status": "healthy"`

### 3. Get Patient ID
```bash
curl http://localhost:8000/api/patients/ | jq '.[0].id'
```

Copy the UUID (e.g., `9f2b1a1a-968a-4bf2-8013-4794ed63451e`)

### 4. Upload Audio Session
```bash
# Replace PATIENT_ID with the UUID from step 3
# Replace /path/to/audio.mp3 with your audio file

curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=PATIENT_ID" \
  -F "file=@/path/to/audio.mp3" | jq
```

Copy the `id` from the response (this is your SESSION_ID)

### 5. Monitor Processing
```bash
# Replace SESSION_ID with the ID from step 4

# Check status (repeat every 10-20 seconds)
curl http://localhost:8000/api/sessions/SESSION_ID | jq '.status'
```

Status progression:
- `uploading` → `transcribing` → `transcribed` → `extracting_notes` → `processed`

Wait until status is `processed` (may take 2-5 minutes)

### 6. View Extracted Notes
```bash
# Get complete session data
curl http://localhost:8000/api/sessions/SESSION_ID | jq

# Get just the notes
curl http://localhost:8000/api/sessions/SESSION_ID/notes | jq

# View therapist summary
curl -s http://localhost:8000/api/sessions/SESSION_ID/notes | jq -r '.therapist_notes'

# View patient summary
curl -s http://localhost:8000/api/sessions/SESSION_ID/notes | jq -r '.patient_summary'

# View key topics
curl -s http://localhost:8000/api/sessions/SESSION_ID/notes | jq '.key_topics'

# View strategies
curl -s http://localhost:8000/api/sessions/SESSION_ID/notes | jq '.strategies'

# View action items
curl -s http://localhost:8000/api/sessions/SESSION_ID/notes | jq '.action_items'
```

---

## Using Interactive API Docs

Prefer a GUI? Use the built-in Swagger UI:

1. Open http://localhost:8000/docs in browser
2. Click on `POST /api/sessions/upload`
3. Click "Try it out"
4. Enter patient_id: `9f2b1a1a-968a-4bf2-8013-4794ed63451e` (from step 3)
5. Click "Choose File" and select your audio
6. Click "Execute"
7. Copy the session_id from the response
8. Click on `GET /api/sessions/{session_id}`
9. Click "Try it out", paste session_id, click "Execute"
10. Repeat step 9 every 10-20 seconds until status is "processed"
11. Once processed, click on `GET /api/sessions/{session_id}/notes`
12. Click "Try it out", paste session_id, click "Execute"
13. Review the extracted notes!

---

## What to Verify

### The extraction should include:

✅ **Key Topics** (3-7 items)
- Should reflect main subjects discussed in the audio

✅ **Topic Summary** (2-3 sentences)
- Concise overview of the session

✅ **Strategies** (if any mentioned)
- Coping techniques, therapeutic interventions
- Categorized (breathing, cognitive, behavioral, etc.)
- Status: introduced, practiced, assigned, or reviewed

✅ **Emotional Themes**
- Main emotions expressed (anxiety, hope, frustration, etc.)

✅ **Triggers** (if any mentioned)
- Situations causing distress
- Severity: mild, moderate, or severe

✅ **Action Items** (homework/tasks)
- Specific, actionable items assigned

✅ **Session Mood**
- Overall tone: very_low, low, neutral, positive, very_positive

✅ **Mood Trajectory**
- improving, declining, stable, or fluctuating

✅ **Therapist Summary**
- 150-200 words
- Clinical, professional tone
- Appropriate for therapist's records

✅ **Patient Summary**
- 100-150 words
- Warm, supportive tone
- Written in second person ("You discussed...")

✅ **Risk Flags** (if applicable)
- Should only flag genuine safety concerns
- Not over-sensitive or under-sensitive

---

## Quality Checklist

After extraction completes, verify:

- [ ] All key fields are populated (not empty arrays)
- [ ] Topics accurately reflect audio content
- [ ] No hallucinated information (check against transcript)
- [ ] Strategies are correctly categorized
- [ ] Action items are specific and actionable
- [ ] Mood assessment seems appropriate
- [ ] Therapist summary is professional and accurate
- [ ] Patient summary is warm and encouraging
- [ ] Risk flags are appropriate (if any)
- [ ] Processing completed in reasonable time (< 5 min for short audio)

---

## Troubleshooting

### "Health check failed"
- Is the server running? Check the terminal
- Try restarting: `uvicorn app.main:app --reload`

### "Patient not found"
- Run: `curl http://localhost:8000/api/patients/ | jq`
- Copy the exact UUID from the response

### "Upload failed"
- Check file format (should be .mp3, .wav, .m4a, etc.)
- Check file size (max 100MB)
- Verify file exists: `ls -lh /path/to/audio.mp3`

### "Processing stuck"
- Check session error: `curl http://localhost:8000/api/sessions/SESSION_ID | jq '.error_message'`
- Check server logs in the terminal
- Verify OpenAI API key is set: `grep OPENAI_API_KEY ../audio-transcription-pipeline/.env`

### "Notes are empty or incomplete"
- Verify transcript exists: `curl http://localhost:8000/api/sessions/SESSION_ID | jq '.transcript_text'`
- Try manual re-extraction: `curl -X POST http://localhost:8000/api/sessions/SESSION_ID/extract-notes`
- Check the transcript has meaningful content (not just silence)

---

## Expected Results

For a typical 1-minute test audio:
- **Upload**: Immediate (< 1 second)
- **Transcription**: ~30-45 seconds
- **Extraction**: ~20-30 seconds
- **Total time**: ~1-2 minutes

For a 30-minute therapy session:
- **Upload**: Immediate (< 1 second)
- **Transcription**: ~3-5 minutes
- **Extraction**: ~20-30 seconds
- **Total time**: ~4-6 minutes

Cost per session: ~$0.20 (Whisper + GPT-4o)

---

## Success!

If you can successfully:
1. ✅ Upload audio
2. ✅ See it progress through all statuses
3. ✅ Get extracted notes with all fields populated
4. ✅ Review quality summaries

**Then your backend is fully working and ready for frontend integration!** 🎉

See `TESTING_GUIDE.md` for comprehensive testing documentation.
