# TherapyBridge Backend - Quick Start Guide

## Setup (One-Time)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy asyncpg openai pytest httpx pydub greenlet
```

## Start Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Server runs on: http://localhost:8000
API docs at: http://localhost:8000/docs

## Quick Test

```bash
# Health check
curl http://localhost:8000/health

# List patients
curl http://localhost:8000/api/patients/

# Get patient ID (save for upload)
curl http://localhost:8000/api/patients/ | python3 -m json.tool | grep '"id"'
```

## Upload Audio Session

```bash
# Replace PATIENT_ID with actual UUID from above
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=PATIENT_ID" \
  -F "file=@/path/to/audio.mp3"
```

Returns session_id immediately. Processing happens in background.

## Check Session Status

```bash
# Replace SESSION_ID with ID from upload response
curl "http://localhost:8000/api/sessions/SESSION_ID" | python3 -m json.tool
```

Status progression:
- `uploading` → `transcribing` → `transcribed` → `extracting_notes` → `processed`

## Get Extracted Notes

```bash
curl "http://localhost:8000/api/sessions/SESSION_ID/notes" | python3 -m json.tool
```

## Run Tests

```bash
# Test AI extraction
pytest tests/test_extraction_service.py::test_extract_notes_basic -v -s

# Test cost estimation
pytest tests/test_extraction_service.py::test_cost_estimation -v
```

## Environment Variables

Located in: `../audio-transcription-pipeline/.env`

Required:
- `DATABASE_URL` - Neon PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key for Whisper + GPT-4o

## Troubleshooting

### Server won't start
```bash
# Check database connection
python -c "import os; from dotenv import load_dotenv; load_dotenv('../audio-transcription-pipeline/.env'); print(os.getenv('DATABASE_URL'))"

# Test database manually
python run_migration.py
```

### Import errors
```bash
# Ensure venv is activated
which python  # Should show path in backend/venv/

# Reinstall dependencies
pip install -r requirements.txt
```

### Upload fails
```bash
# Check patient exists
curl http://localhost:8000/api/patients/

# Check audio file format (should be .mp3, .wav, .m4a, etc.)
file /path/to/audio.mp3

# Check file size (max 100MB)
ls -lh /path/to/audio.mp3
```

## Database Access

```bash
# View tables
psql "$DATABASE_URL" -c "\dt"

# View users
psql "$DATABASE_URL" -c "SELECT * FROM users;"

# View patients
psql "$DATABASE_URL" -c "SELECT * FROM patients;"

# View sessions
psql "$DATABASE_URL" -c "SELECT id, status, audio_filename FROM sessions;"
```

## Cost Monitoring

Each session costs approximately:
- Whisper transcription: $0.006/min
- GPT-4o extraction: $0.02-0.03

30-minute session = ~$0.20 total

Check actual costs in OpenAI dashboard: https://platform.openai.com/usage

## Interactive API Documentation

Open in browser: http://localhost:8000/docs

Features:
- Try all endpoints interactively
- See request/response schemas
- Built-in authorization (when implemented)
- Download OpenAPI spec

## Next Steps

1. Test with a real audio file
2. Verify extraction quality
3. Build frontend dashboard (Day 4)
4. Add authentication
5. Deploy to production
