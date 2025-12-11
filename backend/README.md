# TherapyBridge Backend

FastAPI backend for therapy session management and AI note extraction.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

The backend uses the shared `.env` file from `audio-transcription-pipeline/`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# OpenAI
OPENAI_API_KEY=sk-xxx
```

### 3. Initialize Database

```bash
# Run migration (from backend directory)
python run_migration.py
```

### 4. Run Server

```bash
uvicorn app.main:app --reload
```

API will be available at http://localhost:8000

Interactive docs at http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── database.py          # DB connection
│   ├── models/
│   │   ├── schemas.py       # Pydantic models
│   │   └── db_models.py     # SQLAlchemy models
│   ├── routers/
│   │   ├── sessions.py      # Session endpoints
│   │   └── patients.py      # Patient endpoints
│   └── services/
│       ├── transcription.py # Audio transcription
│       └── note_extraction.py # AI extraction
├── tests/
│   ├── test_extraction_service.py
│   └── fixtures/
│       └── sample_transcripts.py
├── migrations/
│   └── 001_initial_schema.sql
└── requirements.txt
```

## API Endpoints

### Sessions
- `POST /api/sessions/upload` - Upload audio file
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/notes` - Get extracted notes
- `GET /api/sessions` - List all sessions
- `POST /api/sessions/{id}/extract-notes` - Manually trigger extraction

### Patients
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient details
- `GET /api/patients` - List all patients

### Health
- `GET /` - Simple health check
- `GET /health` - Detailed health status

## Testing

### Quick Test (Automated)
```bash
# Test the complete pipeline end-to-end
./test_pipeline.sh

# Or test with your own audio
./test_pipeline.sh /path/to/audio.mp3
```

### Unit Tests
```bash
# Run unit tests
pytest tests/test_extraction_service.py -v

# Run specific test
pytest tests/test_extraction_service.py::test_extract_notes_basic -v
```

### Comprehensive Testing
See detailed testing guides:
- **Quick start**: `TEST_PROMPT.md` - Simple testing steps
- **Full guide**: `TESTING_GUIDE.md` - Complete testing documentation with all edge cases
- **Quick reference**: `QUICKSTART.md` - Common operations

## Usage Example

### Upload Audio Session

```bash
curl -X POST http://localhost:8000/api/sessions/upload \
  -F "file=@session.mp3" \
  -F "patient_id=PATIENT_UUID"
```

### Check Session Status

```bash
curl http://localhost:8000/api/sessions/SESSION_ID
```

### Get Extracted Notes

```bash
curl http://localhost:8000/api/sessions/SESSION_ID/notes
```

## Processing Pipeline

1. **Upload** - Audio file saved, session created with status `uploading`
2. **Transcription** - Whisper API transcribes audio → status `transcribing`
3. **Extraction** - GPT-4o extracts structured notes → status `extracting_notes`
4. **Complete** - All data saved → status `processed`

Processing happens in background after upload returns immediately.

## Cost Estimation

- Whisper API: $0.006/min → **~$0.18** for 30-min session
- GPT-4o extraction: ~$0.01-0.03 per session
- **Total: ~$0.20 per 30-minute session**
