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

## Current Focus: Audio Transcription Pipeline

**Location:** `audio-transcription-pipeline/`

**Full Documentation:** See `Project MDs/TherapyBridge.md`

---

## Repository Structure

```
peerbridge proj/
├── .claude/
│   ├── CLAUDE.md              # Rules + current focus (this file)
│   ├── agents/cl/             # Agent configs
│   └── commands/cl/           # Command configs
├── Project MDs/
│   └── TherapyBridge.md       # MVP + pipeline documentation
└── audio-transcription-pipeline/
    ├── src/pipeline.py
    ├── tests/
    │   ├── test_*.py
    │   ├── samples/
    │   └── outputs/
    ├── scripts/
    ├── README.md
    ├── requirements.txt
    └── .env
```

---

## Current Status

**Pipeline Stages:**
- ✅ Audio preprocessing (single MP3 output)
- ✅ Whisper API transcription (with chunking for >25MB)
- ✅ Speaker diarization (pyannote 4.0)

---

## Quick Commands

```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

---

## Next Steps

- [ ] Integrate diarization into main `src/pipeline.py`
- [ ] Add Therapist/Client speaker labeling
- [ ] Test with >52 min files (chunking verification)

---

## Session Log

### 2025-12-08 - Repository Cleanup
- Added organization rules to CLAUDE.md
- Consolidated all docs into single TherapyBridge.md
- Deleted archive/, docs/, duplicate .claude/, scattered MDs
- Simplified to minimal, high-quality structure
