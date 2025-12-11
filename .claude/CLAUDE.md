# Repository Organization Rules

## Core Principles
1. **Minimize file count** - Every file must earn its place. If info can live in an existing file, it goes there.
2. **One README per component** - Each major folder gets ONE README.md. No additional .md files.
3. **No archive folders** - Old code gets deleted. Git history preserves everything.
4. **No duplicate configs** - Only ONE .claude/ folder at project root.
5. **Value over volume** - Only keep information valuable for project longevity. Delete "might be useful" content.

## What Belongs in a README
- Current state & working features
- Quick start commands
- File structure (if not obvious)
- Key technical decisions & bug fixes worth remembering
- Next steps

## What Does NOT Get Its Own File
- Implementation plans (execute and delete)
- Detailed test logs (summarize critical findings only)
- Removed code archives (use git history)
- Separate "guides" that duplicate README content

## Quality Standard
Before creating any new file, ask:
1. Can this go in an existing README? → Put it there
2. Will this matter in 3 months? → If no, don't create it
3. Does this duplicate existing info? → Delete the duplicate

---

# TherapyBridge - Project State

## Current Focus: Backend AI extraction complete, Frontend dashboard next

**Full Documentation:** See `Project MDs/TherapyBridge.md`

---

## Repository Structure

**Monorepo with 2 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   ├── agents/cl/
│   └── commands/cl/
├── Project MDs/
│   └── TherapyBridge.md       # Master documentation
├── README.md                  # Root README (project overview)
├── .gitignore                 # Root gitignore
├── .python-version            # Root Python version
│
├── audio-transcription-pipeline/  # STANDALONE PROJECT
│   ├── src/
│   │   ├── pipeline.py        # CPU/API pipeline
│   │   ├── pipeline_colab.py  # GPU/Colab pipeline
│   │   ├── gpu_audio_ops.py
│   │   └── performance_logger.py
│   ├── tests/
│   │   ├── test_*.py
│   │   ├── samples/
│   │   └── outputs/           # JSON only
│   ├── scripts/
│   │   ├── setup.sh
│   │   ├── setup_colab.sh
│   │   └── setup_gpu.sh
│   ├── venv/                  # Independent venv
│   ├── .env                   # Pipeline-specific env
│   ├── .env.example
│   ├── .gitignore             # Pipeline-specific
│   ├── .python-version
│   ├── requirements.txt
│   ├── requirements_colab.txt
│   └── README.md
│
└── backend/                   # STANDALONE PROJECT
    ├── app/
    │   ├── main.py
    │   ├── database.py
    │   ├── routers/
    │   ├── models/
    │   └── services/
    ├── tests/
    ├── migrations/
    ├── uploads/audio/         # Runtime only
    ├── venv/                  # Independent venv
    ├── .env                   # Backend-specific env
    ├── .env.example
    ├── .gitignore             # Backend-specific
    ├── .python-version
    ├── requirements.txt
    └── README.md
```

**Key principle:** Each subproject is self-contained and can be deployed independently.

---

## Current Status

**Transcription Pipeline:**
- ✅ Audio preprocessing (CPU & GPU)
- ✅ Whisper transcription (API & local GPU)
- ✅ Speaker diarization (pyannote 3.1)
- ✅ Therapist/Client role labeling

**Backend API:**
- ✅ FastAPI structure
- ✅ Database schema (Neon PostgreSQL)
- ✅ AI note extraction service (GPT-4o)
- ✅ Session endpoints

**Frontend:**
- ⏳ Pending (Next.js + Tailwind)

---

## Quick Commands

**Run transcription pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

**Run backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

---

## Next Steps

- [ ] **CURRENT**: Test Google Colab GPU pipeline (see `thoughts/shared/plans/2025-12-10-colab-gpu-audio-pipeline.md`)
- [ ] Build frontend therapist dashboard
- [ ] Deploy backend to AWS Lambda
- [ ] Integrate frontend with backend API
- [ ] Add authentication (Auth.js)

---

## Session Log

### 2025-12-10 - Google Colab GPU Pipeline Plan
- Created comprehensive plan to fix `torchaudio.AudioMetaData` error
- Root cause: torchaudio 2.9+ removed AudioMetaData class, breaking pyannote.audio 3.x
- Solution: Use pyannote.audio 4.0.3 (uses torchcodec instead of torchaudio)
- Fallback: Pin torch==2.3.1, torchaudio==2.3.1, pyannote.audio==3.3.2
- Plan file: `thoughts/shared/plans/2025-12-10-colab-gpu-audio-pipeline.md`
- Contains 8 copy-paste ready Colab cells with exact code
- Next: Test cells in Colab with compressed-cbt-session.m4a

### 2025-12-10 - Major Cleanup & Monorepo Organization
- Deleted duplicate .claude/ folders in subfolders
- Consolidated 6 scattered Project MDs into TherapyBridge.md
- Removed thoughts/ folder (implementation plans)
- Deleted unused GPU provider scripts (Lambda, Paperspace, RunPod, VastAI)
- Deleted docker/ folder and README_GPU.md (redundant)
- Cleaned test outputs (removed HTML/MD, kept JSON)
- Removed __pycache__ files from backend
- Created .env.example files for both projects
- Created .gitignore and .python-version for backend
- Updated root .gitignore for monorepo structure
- Created root README.md explaining monorepo organization
- Updated CLAUDE.md with accurate structure showing independent projects
- File count reduced by 50+ files
- Final result: Clean monorepo with 2 standalone, deployable projects

### 2025-12-08 - Repository Cleanup
- Added organization rules to CLAUDE.md
- Consolidated all docs into single TherapyBridge.md
- Deleted archive/, docs/, duplicate .claude/, scattered MDs
- Simplified to minimal, high-quality structure
