# Audio Pipeline Consolidation - Executive Summary

**Status:** Design Phase | **Document Version:** 1.0 | **Date:** 2025-12-17

---

## The Problem

Currently have **4 separate pipeline implementations** that duplicate 70% of code:

1. **pipeline.py** - CPU/API mode (289 LOC)
2. **pipeline_gpu.py** - Provider-agnostic GPU (442 LOC)
3. **pipeline_enhanced.py** - Performance logging (656 LOC)
4. **pipeline_colab.py** - Colab-specific (322 LOC)

**Total:** ~1,709 lines of code with ~1,200 lines duplicated

**Impact:**
- Bug fixes require changes in 4 places
- Features must be added 4 times
- Inconsistent behavior across variants
- Confusing for users (which one to use?)

---

## The Solution

**Unified Pipeline with Pluggable Backends**

```
ONE pipeline interface → THREE backend implementations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AudioTranscriptionPipeline (unified API)
    ↓
Backend Auto-Selection
    ↓
┌──────────────┬──────────────┬──────────────┐
│ CPU Backend  │ GPU Backend  │Cloud Backend │
│  (pydub)     │  (torch)     │  (API)       │
└──────────────┴──────────────┴──────────────┘
```

**Key Benefits:**
- **50%+ code reduction** (1,709 → ~1,200 LOC)
- **Single API** for all use cases
- **Auto-detection** of optimal backend
- **Easier maintenance** (fix once, not 4x)
- **Backward compatible** (existing code keeps working)

---

## Architecture Overview

### Core Abstractions

```python
# Abstract Interfaces (contracts)
AudioPreprocessor (ABC)      # Audio loading/normalization
├─ CPUPreprocessor          # pydub implementation
└─ GPUPreprocessor          # torch implementation

Transcriber (ABC)            # Speech-to-text
├─ WhisperAPITranscriber    # OpenAI API
└─ FasterWhisperTranscriber # Local GPU/CPU

Diarizer (ABC)               # Speaker identification
├─ PyAnnoteDiarizer         # pyannote.audio
└─ NullDiarizer            # Disabled mode
```

### Unified Pipeline Usage

```python
# Simple auto-detection (recommended)
from src.pipeline import AudioTranscriptionPipeline

pipeline = AudioTranscriptionPipeline()  # Auto-detects best backend
result = pipeline.process("therapy_session.mp3")

# Explicit backend selection
from src.config import PipelineConfig

config = PipelineConfig(
    backend="gpu",              # "cpu", "gpu", or "cloud"
    enable_diarization=True,
    whisper_model="large-v3"
)
pipeline = AudioTranscriptionPipeline(config=config)
result = pipeline.process("audio.mp3")
```

### Backend Auto-Selection Logic

```
Decision Tree:
1. GPU + faster-whisper installed? → GPU backend (fastest)
2. GPU but no local models?        → Cloud backend (API)
3. No GPU, API key available?      → Cloud backend (API)
4. No GPU, no API key?             → CPU backend (slow, warn user)
```

---

## Migration Plan

**6-8 Week Phased Approach**

```
Phase 1 (Week 1-2): Foundation
✓ Create abstract interfaces
✓ Define data models
✓ Build configuration system

Phase 2 (Week 3-4): Backend Extraction
✓ Extract implementations from old files
✓ CPUPreprocessor, GPUPreprocessor
✓ WhisperAPITranscriber, FasterWhisperTranscriber
✓ PyAnnoteDiarizer

Phase 3 (Week 5): Unified Pipeline
✓ Implement AudioTranscriptionPipeline
✓ Wire up all components
✓ End-to-end testing

Phase 4 (Week 6): Backward Compatibility
✓ Add deprecation shims for old imports
✓ Update CLI (transcribe_gpu.py → transcribe.py)
✓ Migration guide

Phase 5 (Week 7): Testing & Validation
✓ Test coverage >90%
✓ Performance benchmarks
✓ Integration with backend API

Phase 6 (Week 8): Cleanup
✓ Remove old files
✓ Update documentation
```

---

## New Directory Structure

```
audio-transcription-pipeline/
├── src/
│   ├── pipeline.py              # Unified pipeline (NEW)
│   ├── config.py                # Config + backend selection (NEW)
│   ├── interfaces.py            # Abstract base classes (NEW)
│   ├── models.py                # Data models (NEW)
│   │
│   ├── backends/
│   │   ├── preprocessing/
│   │   │   ├── cpu.py          # pydub impl
│   │   │   └── gpu.py          # torch impl
│   │   ├── transcription/
│   │   │   ├── whisper_api.py  # OpenAI API
│   │   │   └── faster_whisper.py # Local
│   │   └── diarization/
│   │       ├── pyannote.py     # pyannote impl
│   │       └── null.py         # No-op
│   │
│   ├── utils/
│   │   ├── alignment.py        # Speaker alignment
│   │   └── chunking.py         # Audio splitting
│   │
│   ├── performance_logger.py   # KEEP (cross-cutting)
│   └── gpu_config.py           # KEEP (used by config.py)
│
├── tests/
│   ├── unit/                   # Component tests
│   ├── integration/            # Backend tests
│   ├── regression/             # Output comparison
│   └── e2e/                    # Full pipeline
│
└── transcribe.py               # Unified CLI (NEW)
```

**Files to Remove (after migration):**
- ❌ pipeline.py (old)
- ❌ pipeline_gpu.py
- ❌ pipeline_enhanced.py
- ❌ pipeline_colab.py
- ❌ transcribe_gpu.py

---

## Code Examples

### Before & After Comparison

**Before (choosing the right pipeline was confusing):**

```python
# CPU/API mode
from pipeline import AudioTranscriptionPipeline
pipeline = AudioTranscriptionPipeline()

# GPU mode
from src.pipeline_gpu import GPUTranscriptionPipeline
pipeline = GPUTranscriptionPipeline(whisper_model="large-v3")

# With logging
from src.pipeline_enhanced import AudioTranscriptionPipeline
pipeline = AudioTranscriptionPipeline(enable_performance_logging=True)

# Different APIs, different imports, confusing!
```

**After (one API for everything):**

```python
from src.pipeline import AudioTranscriptionPipeline
from src.config import PipelineConfig

# Auto-detect (recommended)
pipeline = AudioTranscriptionPipeline()

# Or explicit
config = PipelineConfig(
    backend="gpu",                    # Auto-detected if None
    whisper_model="large-v3",
    enable_performance_logging=True,
    enable_diarization=True
)
pipeline = AudioTranscriptionPipeline(config=config)

# Same API everywhere!
result = pipeline.process("audio.mp3")
```

### CLI Usage

**Before:**
```bash
# Different commands for different modes
python tests/test_full_pipeline.py audio.mp3
python transcribe_gpu.py audio.mp3 --speakers 2
```

**After:**
```bash
# One command, auto-detects backend
python transcribe.py audio.mp3

# Or specify backend explicitly
python transcribe.py audio.mp3 --backend gpu --speakers 2
python transcribe.py audio.mp3 --backend cloud --language es
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance regression | HIGH | Benchmark early, set CI gates, profile hot paths |
| Breaking changes | HIGH | Backward compatibility shims, deprecation warnings |
| Feature gaps | MEDIUM | Feature inventory, regression tests, side-by-side comparison |
| Complexity | LOW | Clear docs, architecture diagrams, examples |
| GPU issues | MEDIUM | Robust detection, graceful fallback, clear errors |

**Rollback Plan:**
- Phases 1-3: No risk (new files only)
- Phase 4+: Shims ensure old code works
- Can revert to old files if critical issues found

---

## Success Criteria

### Quantitative
- ✅ **50%+ LOC reduction** (1,709 → ~1,200)
- ✅ **70%+ duplication elimination**
- ✅ **>90% test coverage**
- ✅ **<5% performance regression**
- ✅ **Zero high-severity bugs**

### Qualitative
- ✅ **Simpler mental model** (1 pipeline vs. 4)
- ✅ **Easier backend switching** (config vs. code rewrite)
- ✅ **Better documentation**
- ✅ **Faster feature development**

---

## Open Questions

1. **Configuration format:** Python API only or also support YAML/TOML?
   - **Recommendation:** Start with Python API + env vars, add YAML later if needed

2. **Backend naming:** "cpu/gpu/cloud" vs. "local-cpu/local-gpu/api"?
   - **Recommendation:** "cpu/gpu/cloud" (simpler, user-centric)

3. **Speaker label mapping:** Keep generic (SPEAKER_00) or map to domain-specific (Therapist/Client)?
   - **Recommendation:** Keep generic, provide optional mapping utility

4. **Performance logging:** Always-on or opt-in?
   - **Recommendation:** Opt-in via config flag (zero overhead when disabled)

---

## Next Steps

### Immediate Actions

1. ✅ **Review design document** with team
2. ⏳ **Get stakeholder approval**
3. ⏳ **Create GitHub issues** (one per phase)
4. ⏳ **Set up development environment**
   - Feature branch: `feature/unified-pipeline`
   - CI/CD pipeline
   - Test environments (CPU + GPU)

### Phase 1 Kickoff (Week 1)

- [ ] Design approved
- [ ] Project board created
- [ ] Feature branch created
- [ ] Test environments ready
- [ ] Team kickoff meeting

---

## Full Design Document

For complete details, see: **[ARCHITECTURE_CONSOLIDATION_DESIGN.md](./ARCHITECTURE_CONSOLIDATION_DESIGN.md)**

Includes:
- Detailed architecture diagrams
- Complete interface specifications
- Migration path examples
- Comprehensive risk assessment
- Testing strategy
- Performance benchmarks
- Decision rationale

---

**Questions?** Review full design doc or contact project lead.

**Timeline:** 6-8 weeks (phased approach, can pause/rollback at any phase)

**Impact:** Massive reduction in code duplication, much easier to maintain going forward.
