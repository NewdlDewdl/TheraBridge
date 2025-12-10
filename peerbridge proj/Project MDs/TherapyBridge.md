# TherapyBridge - Project Documentation

## Overview

TherapyBridge helps therapists manage session recordings through AI-powered transcription and analysis.

**Repository Rules:** See `.claude/CLAUDE.md` for organization standards.

---

## MVP Tech Stack

### Architecture

| Layer | Technology | Cost |
|-------|------------|------|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Free |
| Hosting (Frontend) | Vercel | Free |
| Backend | Python FastAPI | Free |
| Hosting (Backend) | AWS Lambda | ~$1-5/mo |
| Database | Neon PostgreSQL + pgvector | Free tier |
| Auth | Auth.js (NextAuth v5) | Free |
| LLM | Claude Haiku | ~$5-15/mo |
| Transcription | OpenAI Whisper API | Usage-based |
| Diarization | pyannote-audio 4.0 | Free (local) |
| Storage | AWS S3 | ~$1-2/mo |

**Estimated Monthly Cost:** $5-20/month

### MVP Features

- [x] Audio upload (MP3, WAV, M4A)
- [x] Transcription with Whisper API
- [x] Speaker diarization (pyannote)
- [ ] AI note extraction (Claude Haiku)
- [ ] Therapist/Patient dashboards
- [ ] Semantic search

### Deferred to Post-MVP

- Auto speaker diarization improvements
- Background job processing (sync for MVP)
- Real-time transcription
- Advanced cross-session insights
- Crisis detection system
- Mobile app

---

## Audio Transcription Pipeline

**Location:** `audio-transcription-pipeline/`

### Current Status

| Stage | Status | Description |
|-------|--------|-------------|
| Preprocessing | WORKING | MP3 conversion, 16kHz mono, volume normalization |
| Whisper API | WORKING | Timestamped transcription with chunking for >25MB |
| Diarization | WORKING | pyannote 4.0, 2-speaker detection |

### Quick Start

```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

### Test Results (23-min therapy session)

- Input: 21.2MB MP3 → Preprocessed: 10.6MB
- 463 segments transcribed
- 251 speaker turns detected (Therapist: 141, Patient: 110)
- Processing time: ~5.5 minutes

### Pipeline Output Format

```python
{
    "segments": [
        {"start": 0.0, "end": 5.2, "text": "Hello", "speaker": "SPEAKER_00"},
        {"start": 5.2, "end": 8.1, "text": "Hi there", "speaker": "SPEAKER_01"}
    ],
    "full_text": "Hello. Hi there.",
    "duration": 76.3,
    "speaker_turns": [...]
}
```

### Next Steps

- [ ] Integrate diarization into src/pipeline.py
- [ ] Add Therapist/Client role labeling
- [ ] Test with >52 min files (chunking verification)

---

## Environment Setup

### Required API Keys (.env)

```bash
OPENAI_API_KEY=sk-xxx           # Whisper transcription
HF_TOKEN=hf_xxx                 # HuggingFace (pyannote models)
```

### HuggingFace Model Access

Must accept terms for both:
1. https://huggingface.co/pyannote/speaker-diarization-3.1
2. https://huggingface.co/pyannote/speaker-diarization-community-1

### Local Development (Future)

```yaml
# docker-compose.yml structure
services:
  frontend:   # Next.js on port 3000
  backend:    # FastAPI on port 8000
```

---

## Key Technical Decisions

### Why 64kbps MP3?

- Speech doesn't need high bitrate
- Reduces 1-hour file from ~120MB to ~27MB
- Whisper's sweet spot for quality vs. size

### Why pyannote over alternatives?

- Best open-source diarization accuracy
- Runs locally (no API costs)
- Active development, good community

### Pyannote 4.0 Breaking Changes (Critical)

```python
# API parameter changed
Pipeline.from_pretrained(..., token=hf_token)  # NOT use_auth_token

# Output access changed
annotation = diarization.speaker_diarization  # NOT diarization directly
for turn, _, speaker in annotation.itertracks(yield_label=True):
    ...

# TorchCodec workaround - pre-load audio as tensor
import torchaudio
waveform, sample_rate = torchaudio.load(audio_file_path)
audio_dict = {"waveform": waveform, "sample_rate": sample_rate}
diarization = pipeline(audio_dict)  # NOT pipeline(file_path)
```

### File Size Handling

| Duration | MP3 @ 64kbps | Whisper Chunks |
|----------|--------------|----------------|
| 23 min   | ~11 MB       | 1 (no split)   |
| 45 min   | ~22 MB       | 1 (no split)   |
| 60 min   | ~29 MB       | 3 chunks       |
| 90 min   | ~43 MB       | 5 chunks       |

---

## Cost Breakdown (Estimated)

| Service | Free Tier | Overage Cost |
|---------|-----------|--------------|
| Vercel | 100GB bandwidth | $20/100GB |
| Neon | 0.5GB storage | $0.25/GB |
| Claude Haiku | N/A | $0.25/1M input, $1.25/1M output |
| OpenAI Whisper | N/A | $0.006/min |
| AWS S3 | 5GB (12mo) | $0.023/GB |

**Realistic MVP usage (10 sessions/week):** ~$5-10/month
