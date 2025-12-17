# Audio Transcription Pipeline - Architecture Consolidation Design

**Document Version:** 1.0
**Date:** 2025-12-17
**Status:** Design Phase - No Implementation Yet

---

## Executive Summary

This document outlines the design for consolidating multiple pipeline implementations into a single, unified architecture with pluggable backends. The current codebase contains 4 separate pipeline variants (CPU/API, GPU, Enhanced, Colab), resulting in significant code duplication and maintenance overhead.

**Goals:**
- Single pipeline interface with pluggable execution backends
- Eliminate ~70% code duplication across variants
- Maintain backward compatibility with existing integrations
- Enable seamless switching between execution modes (CPU/GPU/Cloud)
- Preserve all existing functionality and performance optimizations

**Estimated Impact:**
- Reduce codebase from ~2000 LOC to ~800 LOC core + ~400 LOC backends
- Simplify testing from 4 separate test suites to 1 unified suite
- Enable easier feature additions (add once vs. 4 times)

---

## 1. Current Architecture Analysis

### 1.1 Existing Pipeline Variants

```
Current State: 4 Independent Pipeline Implementations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────┐
│ 1. pipeline.py (CPU/API)                                │
│    - AudioPreprocessor (pydub)                          │
│    - WhisperTranscriber (OpenAI API)                    │
│    - No diarization                                     │
│    - Use case: Production, cloud deployment             │
│    - Size: ~289 LOC                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 2. pipeline_gpu.py (Provider-Agnostic GPU)              │
│    - GPUAudioProcessor (torch-based)                    │
│    - WhisperModel (faster-whisper local)                │
│    - Pipeline (pyannote diarization)                    │
│    - GPUConfig (auto-detection)                         │
│    - Use case: Vast.ai, RunPod, Lambda, Paperspace     │
│    - Size: ~442 LOC                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 3. pipeline_enhanced.py (Performance Logging)            │
│    - Same as pipeline.py but with PerformanceLogger     │
│    - AudioPreprocessor + logging hooks                  │
│    - WhisperTranscriber + timing                        │
│    - SpeakerDiarizer (optional, GPU-aware)              │
│    - Use case: Research, debugging                      │
│    - Size: ~656 LOC                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 4. pipeline_colab.py (Colab L4 Optimized)               │
│    - Hardcoded for Colab paths (/content/...)          │
│    - GPUAudioProcessor                                  │
│    - WhisperModel (faster-whisper)                      │
│    - Pipeline (pyannote)                                │
│    - Use case: Google Colab notebooks                   │
│    - Size: ~322 LOC                                     │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Shared vs. Unique Functionality

**Shared Functionality (Duplicated 4x):**
```
┌────────────────────────────────────────────────────────┐
│ DUPLICATED ACROSS ALL VARIANTS                         │
├────────────────────────────────────────────────────────┤
│ ✓ Audio loading/validation                            │
│ ✓ Format conversion                                   │
│ ✓ Sample rate conversion                              │
│ ✓ Mono conversion                                     │
│ ✓ Result formatting (JSON structure)                  │
│ ✓ Error handling patterns                             │
│ ✓ Logging/output formatting                           │
└────────────────────────────────────────────────────────┘
```

**Preprocessing Variants:**
```
CPU (pydub):               GPU (torch):
┌──────────────┐          ┌──────────────┐
│ AudioSegment │          │ torchaudio   │
│ detect_silence│          │ torch ops    │
│ normalize()  │          │ GPU kernels  │
└──────────────┘          └──────────────┘
      ↓                          ↓
  [Different implementations, same outcome]
```

**Transcription Variants:**
```
API (OpenAI):              Local (faster-whisper):
┌──────────────┐          ┌──────────────┐
│ HTTP upload  │          │ Local model  │
│ Remote GPU   │          │ GPU/CPU      │
│ Paid API     │          │ Free         │
└──────────────┘          └──────────────┘
```

**Diarization Variants:**
```
Optional (enhanced):       Always-on (GPU):       None (simple):
┌──────────────┐          ┌──────────────┐       ┌──────────────┐
│ if enabled   │          │ always runs  │       │ not available│
│ CPU/GPU      │          │ GPU only     │       │              │
└──────────────┘          └──────────────┘       └──────────────┘
```

### 1.3 Dependency Analysis

```
Component Dependencies:
━━━━━━━━━━━━━━━━━━━━━━━━

AudioPreprocessor
├─ pydub (CPU variant)
│  ├─ ffmpeg (system)
│  └─ audioop-lts
└─ torch + torchaudio (GPU variant)
   ├─ julius (GPU resampling)
   └─ CUDA runtime

WhisperTranscriber
├─ openai (API variant)
│  └─ OPENAI_API_KEY
└─ faster-whisper (local variant)
   ├─ ctranslate2
   └─ CUDA (optional)

SpeakerDiarizer
└─ pyannote.audio
   ├─ torch
   ├─ HF_TOKEN
   └─ CUDA/MPS (optional)

PerformanceLogger
├─ psutil (optional)
├─ GPUtil (optional)
└─ torch (for GPU monitoring)

GPUConfig
└─ torch
   └─ CUDA
```

### 1.4 Code Duplication Metrics

```
Duplication Analysis:
━━━━━━━━━━━━━━━━━━━━

Total LOC: ~1,709 (across 4 files)
Estimated Duplication: ~1,200 LOC (70%)

Breakdown:
- Audio validation logic: 4x duplicated (~120 LOC)
- Result formatting: 4x duplicated (~100 LOC)
- Error handling: 4x duplicated (~80 LOC)
- Pipeline orchestration: 4x similar (~400 LOC)
- Logging/output: 4x duplicated (~200 LOC)
- Speaker alignment: 3x duplicated (~300 LOC)

Unique functionality per variant: ~30%
- GPU optimizations (pipeline_gpu.py)
- Performance logging hooks (pipeline_enhanced.py)
- Provider detection (gpu_config.py)
- API-specific chunking (pipeline.py)
```

### 1.5 Current Issues

**Maintenance Burden:**
- Bug fixes require changes in 4 places
- Feature additions must be replicated 4x
- Testing requires 4 separate test suites
- Documentation fragmentation

**Inconsistencies:**
- Different error messages across variants
- Inconsistent output formats
- Different default parameters
- Varying validation logic

**User Confusion:**
- Which pipeline to use when?
- How to switch between modes?
- Different APIs for same functionality

---

## 2. Proposed Unified Architecture

### 2.1 High-Level Design

```
Unified Pipeline Architecture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  AudioTranscriptionPipeline (Unified API)             │  │
│  │  - Single entry point                                 │  │
│  │  - Auto-detects optimal backend                       │  │
│  │  - Consistent interface across all modes              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   ABSTRACTION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Preprocessor │  │ Transcriber  │  │  Diarizer    │      │
│  │  Interface   │  │  Interface   │  │  Interface   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND IMPLEMENTATIONS                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CPU Backend  │  │ GPU Backend  │  │ Cloud Backend│      │
│  │ (pydub)      │  │ (torch)      │  │ (API)        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   CROSS-CUTTING CONCERNS                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Performance  │  │ Config Mgmt  │  │   Logging    │      │
│  │   Logger     │  │ (auto-detect)│  │   System     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interfaces

#### 2.2.1 Core Pipeline Interface

```python
class AudioTranscriptionPipeline:
    """
    Unified pipeline with automatic backend selection.

    Design Principles:
    - Single entry point for all use cases
    - Automatic backend detection based on environment
    - Manual backend override support
    - Consistent API across all modes
    """

    def __init__(
        self,
        backend: Optional[str] = None,  # "cpu", "gpu", "cloud", None=auto
        enable_diarization: bool = True,
        enable_performance_logging: bool = False,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize pipeline with optional backend override.

        Auto-detection hierarchy:
        1. GPU available + local models → GPU backend
        2. GPU available + no models → Cloud backend (API)
        3. No GPU → CPU backend
        """
        pass

    def process(
        self,
        audio_path: str,
        language: Optional[str] = None,
        num_speakers: int = 2,
        **kwargs
    ) -> TranscriptionResult:
        """
        Process audio file through complete pipeline.

        Returns:
            TranscriptionResult with segments, speaker labels, metadata
        """
        pass
```

#### 2.2.2 Preprocessor Interface

```python
class AudioPreprocessor(ABC):
    """
    Abstract base class for audio preprocessing.

    Contract:
    - Load audio from any common format
    - Convert to mono 16kHz
    - Trim silence (optional)
    - Normalize volume (optional)
    - Return path to processed audio
    """

    @abstractmethod
    def preprocess(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        trim_silence: bool = True,
        normalize: bool = True
    ) -> str:
        """
        Preprocess audio file.

        Args:
            audio_path: Input audio file
            output_path: Where to save processed audio (None = auto)
            trim_silence: Whether to trim leading/trailing silence
            normalize: Whether to normalize volume

        Returns:
            Path to processed audio file
        """
        pass

    @abstractmethod
    def validate(self, audio_path: str) -> AudioMetadata:
        """Validate and extract metadata from audio file."""
        pass


class CPUPreprocessor(AudioPreprocessor):
    """pydub-based implementation (CPU)."""
    pass


class GPUPreprocessor(AudioPreprocessor):
    """torch/torchaudio-based implementation (GPU)."""
    pass
```

#### 2.2.3 Transcriber Interface

```python
class Transcriber(ABC):
    """
    Abstract base class for speech-to-text transcription.

    Contract:
    - Accept preprocessed audio
    - Return timestamped segments
    - Support language specification
    - Handle chunking internally if needed
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionData:
        """
        Transcribe audio to text with timestamps.

        Returns:
            TranscriptionData with segments, full_text, language, duration
        """
        pass


class WhisperAPITranscriber(Transcriber):
    """OpenAI Whisper API implementation."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_path: str, language: Optional[str] = None):
        # Auto-chunking for >25MB files
        # API call with retries
        pass


class FasterWhisperTranscriber(Transcriber):
    """faster-whisper local implementation (GPU/CPU)."""

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "int8"
    ):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None):
        # Local inference
        pass
```

#### 2.2.4 Diarizer Interface

```python
class Diarizer(ABC):
    """
    Abstract base class for speaker diarization.

    Contract:
    - Accept preprocessed audio
    - Return speaker turn segments
    - Support configurable number of speakers
    - GPU acceleration when available
    """

    @abstractmethod
    def diarize(
        self,
        audio_path: str,
        num_speakers: int = 2
    ) -> List[SpeakerTurn]:
        """
        Identify speaker turns in audio.

        Returns:
            List of SpeakerTurn objects with speaker, start, end
        """
        pass


class PyAnnoteDiarizer(Diarizer):
    """pyannote.audio implementation (GPU-aware)."""

    def __init__(self, hf_token: str):
        from pyannote.audio import Pipeline
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )
        # Auto-detect GPU
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
        elif torch.backends.mps.is_available():
            self.pipeline.to(torch.device("mps"))

    def diarize(self, audio_path: str, num_speakers: int = 2):
        # Run diarization
        pass


class NullDiarizer(Diarizer):
    """No-op diarizer for when diarization is disabled."""

    def diarize(self, audio_path: str, num_speakers: int = 2):
        return []  # Empty speaker turns
```

#### 2.2.5 Data Models

```python
@dataclass
class AudioMetadata:
    """Audio file metadata."""
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    file_size_mb: float
    valid: bool
    error: Optional[str] = None


@dataclass
class TranscriptionSegment:
    """Single transcription segment."""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


@dataclass
class SpeakerTurn:
    """Speaker turn segment."""
    speaker: str
    start: float
    end: float


@dataclass
class TranscriptionData:
    """Raw transcription output."""
    segments: List[TranscriptionSegment]
    full_text: str
    language: str
    duration: float


@dataclass
class TranscriptionResult:
    """Complete pipeline output."""
    segments: List[TranscriptionSegment]
    aligned_segments: List[TranscriptionSegment]  # With speaker labels
    speaker_turns: List[SpeakerTurn]
    full_text: str
    language: str
    duration: float
    metadata: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]] = None
```

### 2.3 Backend Selection Logic

```python
class BackendSelector:
    """
    Automatic backend selection based on environment.

    Decision Tree:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    1. Check for explicit backend override
       └─> If specified, use that backend

    2. Check for GPU availability
       ├─> CUDA available?
       │   ├─> faster-whisper installed?
       │   │   └─> Use GPU backend (local)
       │   └─> faster-whisper not installed?
       │       └─> Use Cloud backend (API)
       │
       └─> No CUDA
           ├─> OpenAI API key available?
           │   └─> Use Cloud backend
           └─> No API key
               └─> Use CPU backend (warn about slow performance)

    3. Check for diarization requirements
       └─> If enabled, verify HF_TOKEN available
    """

    @staticmethod
    def select_backend(
        backend_override: Optional[str] = None,
        enable_diarization: bool = True
    ) -> str:
        """
        Select optimal backend for current environment.

        Returns:
            Backend name: "cpu", "gpu", or "cloud"
        """
        # Explicit override
        if backend_override:
            if backend_override not in ["cpu", "gpu", "cloud"]:
                raise ValueError(f"Invalid backend: {backend_override}")
            return backend_override

        # Auto-detection
        if torch.cuda.is_available():
            try:
                import faster_whisper
                return "gpu"  # GPU + local models available
            except ImportError:
                if os.getenv("OPENAI_API_KEY"):
                    return "cloud"  # GPU but no local models, use API
                else:
                    raise RuntimeError(
                        "GPU available but neither faster-whisper nor "
                        "OPENAI_API_KEY found. Install faster-whisper or "
                        "set OPENAI_API_KEY."
                    )
        else:
            if os.getenv("OPENAI_API_KEY"):
                return "cloud"  # No GPU, use API
            else:
                warnings.warn(
                    "No GPU and no OPENAI_API_KEY. Using CPU backend "
                    "(very slow). Consider setting OPENAI_API_KEY."
                )
                return "cpu"

    @staticmethod
    def create_components(backend: str, config: PipelineConfig):
        """
        Factory method to create backend-specific components.

        Returns:
            (preprocessor, transcriber, diarizer) tuple
        """
        if backend == "cpu":
            return (
                CPUPreprocessor(),
                WhisperAPITranscriber(api_key=config.openai_api_key),
                PyAnnoteDiarizer(hf_token=config.hf_token) if config.enable_diarization else NullDiarizer()
            )

        elif backend == "gpu":
            return (
                GPUPreprocessor(device="cuda"),
                FasterWhisperTranscriber(
                    model_size=config.whisper_model,
                    device="cuda",
                    compute_type=config.compute_type
                ),
                PyAnnoteDiarizer(hf_token=config.hf_token) if config.enable_diarization else NullDiarizer()
            )

        elif backend == "cloud":
            return (
                CPUPreprocessor(),  # Minimal preprocessing for API
                WhisperAPITranscriber(api_key=config.openai_api_key),
                PyAnnoteDiarizer(hf_token=config.hf_token) if config.enable_diarization else NullDiarizer()
            )
```

### 2.4 Configuration System

```python
@dataclass
class PipelineConfig:
    """
    Unified configuration for all pipeline modes.

    Design: Single config object that adapts based on backend.
    """
    # Backend selection
    backend: Optional[str] = None  # None = auto-detect

    # API credentials
    openai_api_key: Optional[str] = None
    hf_token: Optional[str] = None

    # Whisper configuration
    whisper_model: str = "large-v3"  # For local inference
    language: Optional[str] = None  # None = auto-detect

    # Diarization configuration
    enable_diarization: bool = True
    num_speakers: int = 2

    # GPU configuration (auto-detected, can override)
    compute_type: str = "int8"  # "float16", "int8", "float32"
    device: str = "cuda"  # "cuda", "mps", "cpu"

    # Preprocessing options
    trim_silence: bool = True
    normalize_audio: bool = True
    target_sample_rate: int = 16000
    target_format: str = "wav"  # "wav" or "mp3"

    # Performance options
    enable_performance_logging: bool = False
    num_workers: int = 4
    batch_size: int = 8

    # Output options
    output_dir: Optional[str] = None
    save_intermediate: bool = False

    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Create config from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            hf_token=os.getenv("HF_TOKEN"),
            # ... other env vars
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.

        Returns:
            List of validation messages
        """
        messages = []

        # Check credentials based on backend needs
        if self.backend in [None, "cloud"]:
            if not self.openai_api_key:
                messages.append("OPENAI_API_KEY not set (required for cloud backend)")

        if self.enable_diarization and not self.hf_token:
            messages.append("HF_TOKEN not set (required for diarization)")

        return messages
```

### 2.5 Directory Structure

```
audio-transcription-pipeline/
├── src/
│   ├── __init__.py
│   │
│   ├── pipeline.py                    # NEW: Unified pipeline
│   │   └─ AudioTranscriptionPipeline
│   │
│   ├── config.py                      # NEW: Configuration system
│   │   ├─ PipelineConfig
│   │   └─ BackendSelector
│   │
│   ├── interfaces.py                  # NEW: Abstract interfaces
│   │   ├─ AudioPreprocessor (ABC)
│   │   ├─ Transcriber (ABC)
│   │   └─ Diarizer (ABC)
│   │
│   ├── models.py                      # NEW: Data models
│   │   ├─ AudioMetadata
│   │   ├─ TranscriptionSegment
│   │   ├─ SpeakerTurn
│   │   ├─ TranscriptionData
│   │   └─ TranscriptionResult
│   │
│   ├── backends/
│   │   ├── __init__.py
│   │   │
│   │   ├── preprocessing/
│   │   │   ├── cpu.py                 # CPUPreprocessor (pydub)
│   │   │   └── gpu.py                 # GPUPreprocessor (torch)
│   │   │
│   │   ├── transcription/
│   │   │   ├── whisper_api.py         # WhisperAPITranscriber
│   │   │   └── faster_whisper.py      # FasterWhisperTranscriber
│   │   │
│   │   └── diarization/
│   │       ├── pyannote.py            # PyAnnoteDiarizer
│   │       └── null.py                # NullDiarizer
│   │
│   ├── utils/
│   │   ├── audio.py                   # Audio utilities (shared)
│   │   ├── alignment.py               # Speaker alignment logic
│   │   └── chunking.py                # Audio chunking for API limits
│   │
│   ├── performance_logger.py          # KEEP: Performance monitoring
│   └── gpu_config.py                  # KEEP: GPU detection (used by config.py)
│
├── tests/
│   ├── test_pipeline.py               # NEW: Unified pipeline tests
│   ├── test_backends.py               # NEW: Backend-specific tests
│   ├── test_config.py                 # NEW: Config system tests
│   └── samples/                       # Existing test samples
│
├── scripts/
│   ├── setup.sh
│   └── setup_gpu.sh
│
├── transcribe.py                      # NEW: Unified CLI (replaces transcribe_gpu.py)
├── requirements.txt                   # Core dependencies
├── requirements-gpu.txt               # GPU-specific dependencies
└── README.md
```

---

## 3. Migration Strategy

### 3.1 Phased Approach

```
Migration Phases (6-8 weeks total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1: Foundation (Week 1-2)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Create abstract interfaces                               │
│ - Define data models                                       │
│ - Build configuration system                               │
│ - Set up new directory structure                           │
│                                                            │
│ Deliverables:                                              │
│ ✓ src/interfaces.py                                        │
│ ✓ src/models.py                                            │
│ ✓ src/config.py                                            │
│ ✓ Unit tests for each                                      │
│                                                            │
│ Risk: Low (no existing code affected)                      │
└────────────────────────────────────────────────────────────┘

PHASE 2: Backend Extraction (Week 3-4)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Extract CPU preprocessing from pipeline.py               │
│ - Extract GPU preprocessing from pipeline_gpu.py           │
│ - Extract API transcriber from pipeline.py                 │
│ - Extract local transcriber from pipeline_gpu.py           │
│ - Extract diarizer from pipeline_enhanced.py               │
│                                                            │
│ Deliverables:                                              │
│ ✓ src/backends/preprocessing/cpu.py                        │
│ ✓ src/backends/preprocessing/gpu.py                        │
│ ✓ src/backends/transcription/whisper_api.py               │
│ ✓ src/backends/transcription/faster_whisper.py            │
│ ✓ src/backends/diarization/pyannote.py                     │
│ ✓ Integration tests for each backend                       │
│                                                            │
│ Risk: Medium (ensure feature parity with originals)        │
└────────────────────────────────────────────────────────────┘

PHASE 3: Unified Pipeline (Week 5)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Implement AudioTranscriptionPipeline                     │
│ - Implement BackendSelector                                │
│ - Implement speaker alignment (shared utility)             │
│ - Wire up all components                                   │
│                                                            │
│ Deliverables:                                              │
│ ✓ src/pipeline.py (new unified version)                    │
│ ✓ src/utils/alignment.py                                   │
│ ✓ src/utils/chunking.py                                    │
│ ✓ End-to-end tests (all backends)                          │
│                                                            │
│ Risk: Medium (integration complexity)                      │
└────────────────────────────────────────────────────────────┘

PHASE 4: Backward Compatibility (Week 6)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Create compatibility shims for old imports               │
│ - Update CLI tools (transcribe_gpu.py → transcribe.py)    │
│ - Update test scripts to use new API                       │
│ - Document migration path for users                        │
│                                                            │
│ Deliverables:                                              │
│ ✓ Deprecation warnings in old files                        │
│ ✓ Import redirects (pipeline.py → src/pipeline.py)        │
│ ✓ Updated transcribe.py CLI                                │
│ ✓ MIGRATION_GUIDE.md                                       │
│                                                            │
│ Risk: Low (additive changes only)                          │
└────────────────────────────────────────────────────────────┘

PHASE 5: Testing & Validation (Week 7)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Comprehensive test coverage (>90%)                       │
│ - Performance benchmarking (vs. old implementations)       │
│ - Integration testing with backend API                     │
│ - User acceptance testing                                  │
│                                                            │
│ Deliverables:                                              │
│ ✓ Test suite passing on all backends                       │
│ ✓ Performance regression tests                             │
│ ✓ Integration test with /backend API                       │
│ ✓ Test reports and metrics                                 │
│                                                            │
│ Risk: Medium (need to ensure no regressions)               │
└────────────────────────────────────────────────────────────┘

PHASE 6: Cleanup & Documentation (Week 8)
┌────────────────────────────────────────────────────────────┐
│ Goals:                                                      │
│ - Remove old pipeline files                                │
│ - Update README with new architecture                      │
│ - Create comprehensive docs                                │
│ - Update examples and tutorials                            │
│                                                            │
│ Deliverables:                                              │
│ ✓ Delete pipeline.py, pipeline_gpu.py, etc.               │
│ ✓ Updated README.md                                        │
│ ✓ ARCHITECTURE.md (this document, updated)                 │
│ ✓ API_REFERENCE.md                                         │
│ ✓ EXAMPLES.md                                              │
│                                                            │
│ Risk: Low (cleanup only)                                   │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Backward Compatibility Strategy

**Goal:** Existing code continues working during transition period.

**Approach: Deprecation Shims**

```python
# OLD: pipeline.py (deprecated)
import warnings
from src.pipeline import AudioTranscriptionPipeline as _NewPipeline
from src.config import PipelineConfig

warnings.warn(
    "Importing from 'pipeline.py' is deprecated. "
    "Use 'from src.pipeline import AudioTranscriptionPipeline' instead.",
    DeprecationWarning,
    stacklevel=2
)

class AudioTranscriptionPipeline(_NewPipeline):
    """
    Backward compatibility wrapper.

    This class is deprecated and will be removed in v2.0.
    Please use src.pipeline.AudioTranscriptionPipeline instead.
    """

    def __init__(self):
        warnings.warn(
            "This import path is deprecated. Update your code.",
            DeprecationWarning
        )
        # Create config with CPU backend to match old behavior
        config = PipelineConfig(backend="cpu", enable_diarization=False)
        super().__init__(config=config)


# Similar shims for other deprecated files...
```

**Import Redirects:**

```python
# For users doing: from pipeline import AudioPreprocessor
__all__ = ["AudioTranscriptionPipeline", "AudioPreprocessor", "WhisperTranscriber"]

from src.pipeline import AudioTranscriptionPipeline
from src.backends.preprocessing.cpu import CPUPreprocessor as AudioPreprocessor
from src.backends.transcription.whisper_api import WhisperAPITranscriber as WhisperTranscriber
```

**CLI Compatibility:**

```bash
# OLD: transcribe_gpu.py (deprecated)
#!/usr/bin/env python3
echo "WARNING: transcribe_gpu.py is deprecated. Use 'transcribe.py --backend gpu' instead."
python transcribe.py --backend gpu "$@"
```

### 3.3 Testing Strategy

**Test Coverage Goals:**
- Unit tests: >95% coverage
- Integration tests: All backend combinations
- Regression tests: Match old pipeline outputs exactly

**Test Pyramid:**

```
Testing Strategy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         ╱╲
        ╱ E╲       E2E Tests (5%)
       ╱────╲      - Full pipeline (all backends)
      ╱  I   ╲     - Real audio files
     ╱────────╲    - Performance benchmarks
    ╱  Integration ╲   Integration Tests (15%)
   ╱──────────────╲    - Backend combinations
  ╱    Unit Tests   ╲   - Component interactions
 ╱──────────────────╲
╱     (80%)          ╲  Unit Tests (80%)
━━━━━━━━━━━━━━━━━━━━━━  - Individual classes
                        - Mock external dependencies
                        - Fast execution (<1s total)
```

**Test Categories:**

1. **Unit Tests** (`tests/unit/`)
   ```python
   # Test individual components in isolation

   def test_cpu_preprocessor_trim_silence():
       preprocessor = CPUPreprocessor()
       # Test with mock audio
       pass

   def test_whisper_api_transcriber_chunking():
       transcriber = WhisperAPITranscriber(api_key="fake")
       # Test chunking logic with mock API
       pass

   def test_backend_selector_auto_detection():
       # Mock torch.cuda.is_available()
       # Verify correct backend selected
       pass
   ```

2. **Integration Tests** (`tests/integration/`)
   ```python
   # Test component interactions

   def test_cpu_backend_full_pipeline():
       config = PipelineConfig(backend="cpu")
       pipeline = AudioTranscriptionPipeline(config)
       result = pipeline.process("test.mp3")
       assert result.segments
       # Verify output matches old pipeline.py

   def test_gpu_backend_with_diarization():
       config = PipelineConfig(backend="gpu", enable_diarization=True)
       # Requires GPU + HF_TOKEN
       pass
   ```

3. **Regression Tests** (`tests/regression/`)
   ```python
   # Ensure outputs match old implementations

   def test_output_parity_cpu():
       """Verify new CPU backend matches old pipeline.py."""
       # Run same audio through both
       # Compare outputs (should be identical)
       pass

   def test_performance_parity_gpu():
       """Verify new GPU backend matches old pipeline_gpu.py."""
       # Benchmark against old implementation
       # Allow 5% performance variance
       pass
   ```

4. **E2E Tests** (`tests/e2e/`)
   ```python
   # Full pipeline with real audio

   def test_therapy_session_transcription():
       """Test with actual therapy session audio."""
       config = PipelineConfig.from_env()
       pipeline = AudioTranscriptionPipeline(config)
       result = pipeline.process("samples/therapy_session.mp3")

       # Verify expected outputs
       assert result.language == "en"
       assert len(result.aligned_segments) > 10
       assert "SPEAKER_00" in [s.speaker for s in result.aligned_segments]
   ```

**Continuous Integration:**

```yaml
# .github/workflows/test.yml

name: Test Suite
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=html

  integration-tests-cpu:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run CPU backend tests
        run: pytest tests/integration/ -v -m "cpu"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  integration-tests-gpu:
    runs-on: self-hosted  # GPU runner
    steps:
      - uses: actions/checkout@v2
      - name: Run GPU backend tests
        run: pytest tests/integration/ -v -m "gpu"
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}

  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Compare with baseline outputs
        run: pytest tests/regression/ -v
```

---

## 4. Component Interface Specifications

### 4.1 Preprocessor Contract

```python
class AudioPreprocessor(ABC):
    """
    Contract for audio preprocessing implementations.

    Responsibilities:
    - Load audio from file system
    - Validate audio format and metadata
    - Apply transformations (silence trimming, normalization, resampling)
    - Export processed audio

    Implementations:
    - CPUPreprocessor: Uses pydub + ffmpeg (CPU-bound)
    - GPUPreprocessor: Uses torch + torchaudio (GPU-accelerated)

    Common Interface:
    All implementations must support the same method signatures
    and return identical data structures.
    """

    @abstractmethod
    def preprocess(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        trim_silence: bool = True,
        normalize: bool = True,
        target_sample_rate: int = 16000,
        target_format: str = "wav"
    ) -> str:
        """
        Preprocess audio file.

        Args:
            audio_path: Path to input audio file
            output_path: Path for output (None = auto-generate)
            trim_silence: Whether to trim leading/trailing silence
            normalize: Whether to normalize volume
            target_sample_rate: Resample to this rate (Hz)
            target_format: Output format ("wav" or "mp3")

        Returns:
            Path to processed audio file

        Raises:
            FileNotFoundError: If audio_path doesn't exist
            ValueError: If audio file is invalid or corrupted
            RuntimeError: If preprocessing fails

        Guarantees:
        - Output is always mono
        - Output sample rate matches target_sample_rate
        - Output format matches target_format
        - Output file size is reasonable (<100MB for typical sessions)
        """
        pass

    @abstractmethod
    def validate(self, audio_path: str) -> AudioMetadata:
        """
        Validate audio file and extract metadata.

        Args:
            audio_path: Path to audio file

        Returns:
            AudioMetadata object with validation results

        Note:
        - Should NOT raise exceptions on invalid files
        - Instead, return AudioMetadata with valid=False and error message
        """
        pass

    def _trim_silence(
        self,
        audio: Any,  # Type varies by implementation
        threshold_db: float = -40.0,
        min_silence_duration: float = 0.5
    ) -> Any:
        """
        Remove leading and trailing silence.

        Protected method - implementation-specific.
        """
        pass

    def _normalize(
        self,
        audio: Any,
        target_db: float = -20.0,
        headroom: float = 0.1
    ) -> Any:
        """
        Normalize audio volume.

        Protected method - implementation-specific.
        """
        pass
```

### 4.2 Transcriber Contract

```python
class Transcriber(ABC):
    """
    Contract for speech-to-text transcription implementations.

    Responsibilities:
    - Convert speech to text with timestamps
    - Handle automatic language detection
    - Manage model loading and resource cleanup
    - Handle API rate limits / retries (if applicable)

    Implementations:
    - WhisperAPITranscriber: OpenAI Whisper API (cloud)
    - FasterWhisperTranscriber: faster-whisper (local GPU/CPU)

    Performance Expectations:
    - API: ~0.2x real-time (5min audio = 1min processing)
    - GPU: ~10-30x real-time (5min audio = 10-30sec processing)
    - CPU: ~0.1x real-time (5min audio = 50min processing)
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionData:
        """
        Transcribe audio to text with timestamps.

        Args:
            audio_path: Path to preprocessed audio file
            language: ISO 639-1 language code (None = auto-detect)

        Returns:
            TranscriptionData with:
            - segments: List of timestamped text segments
            - full_text: Complete transcription
            - language: Detected/specified language code
            - duration: Audio duration in seconds

        Raises:
            FileNotFoundError: If audio_path doesn't exist
            RuntimeError: If transcription fails
            ConnectionError: If API is unavailable (API transcribers only)

        Guarantees:
        - Segments are ordered by start time
        - Segments don't overlap (exclusive timestamps)
        - full_text is concatenation of all segment texts
        - duration matches audio file duration (±1%)
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Release resources (models, GPU memory, connections).

        Called when pipeline is destroyed or switching backends.
        Implementations should:
        - Unload models from memory
        - Clear GPU cache
        - Close API connections
        """
        pass

    def _validate_audio(self, audio_path: str):
        """
        Validate audio file before transcription.

        Protected method - can be overridden for backend-specific checks.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        if file_size_mb > 1000:  # 1GB sanity check
            raise ValueError(f"Audio file too large: {file_size_mb:.1f}MB")
```

### 4.3 Diarizer Contract

```python
class Diarizer(ABC):
    """
    Contract for speaker diarization implementations.

    Responsibilities:
    - Identify speaker changes in audio
    - Group speech segments by speaker
    - Handle variable number of speakers
    - Utilize GPU when available

    Implementations:
    - PyAnnoteDiarizer: pyannote.audio (GPU-accelerated)
    - NullDiarizer: No-op implementation when diarization disabled

    Performance Expectations:
    - GPU: ~1-2x real-time (5min audio = 5-10min processing)
    - CPU: ~0.1x real-time (5min audio = 50min processing)
    """

    @abstractmethod
    def diarize(
        self,
        audio_path: str,
        num_speakers: int = 2
    ) -> List[SpeakerTurn]:
        """
        Identify speaker turns in audio.

        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers

        Returns:
            List of SpeakerTurn objects with:
            - speaker: Speaker ID (e.g., "SPEAKER_00", "SPEAKER_01")
            - start: Start time in seconds
            - end: End time in seconds

        Raises:
            FileNotFoundError: If audio_path doesn't exist
            RuntimeError: If diarization fails

        Guarantees:
        - Turns are ordered by start time
        - Speaker IDs are consistent throughout audio
        - Turns may overlap (multiple speakers talking)
        - Total turn duration ≤ audio duration
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Release resources (models, GPU memory).

        Called when pipeline is destroyed or switching backends.
        """
        pass
```

---

## 5. Migration Path Examples

### 5.1 Current Usage → New Unified API

**Before (CPU/API pipeline):**
```python
# OLD: Direct import from pipeline.py
from pipeline import AudioTranscriptionPipeline

pipeline = AudioTranscriptionPipeline()
result = pipeline.process("audio.mp3")
print(result['full_text'])
```

**After (Unified API):**
```python
# NEW: Import from src.pipeline
from src.pipeline import AudioTranscriptionPipeline
from src.config import PipelineConfig

# Option 1: Auto-detect backend
pipeline = AudioTranscriptionPipeline()
result = pipeline.process("audio.mp3")
print(result.full_text)  # Note: attribute access instead of dict

# Option 2: Explicit CPU backend
config = PipelineConfig(backend="cpu")
pipeline = AudioTranscriptionPipeline(config=config)
result = pipeline.process("audio.mp3")
```

**Before (GPU pipeline):**
```python
# OLD: Direct import from pipeline_gpu.py
from src.pipeline_gpu import GPUTranscriptionPipeline

pipeline = GPUTranscriptionPipeline(whisper_model="large-v3")
result = pipeline.process(
    "audio.mp3",
    num_speakers=2,
    language="en",
    enable_diarization=True
)
```

**After (Unified API):**
```python
# NEW: Same unified API
from src.pipeline import AudioTranscriptionPipeline
from src.config import PipelineConfig

config = PipelineConfig(
    backend="gpu",  # Explicit GPU backend
    whisper_model="large-v3",
    enable_diarization=True,
    num_speakers=2
)
pipeline = AudioTranscriptionPipeline(config=config)
result = pipeline.process("audio.mp3", language="en")
```

### 5.2 Environment-Based Configuration

**Before (manual selection):**
```python
import torch

if torch.cuda.is_available():
    from src.pipeline_gpu import GPUTranscriptionPipeline as Pipeline
else:
    from pipeline import AudioTranscriptionPipeline as Pipeline

pipeline = Pipeline()
# ... different initialization for each variant
```

**After (automatic):**
```python
from src.pipeline import AudioTranscriptionPipeline
from src.config import PipelineConfig

# Auto-detects GPU and selects optimal backend
config = PipelineConfig.from_env()
pipeline = AudioTranscriptionPipeline(config=config)

# Always the same API, regardless of backend
result = pipeline.process("audio.mp3")
```

### 5.3 CLI Migration

**Before:**
```bash
# CPU/API mode
python tests/test_full_pipeline.py audio.mp3

# GPU mode
python transcribe_gpu.py audio.mp3 --speakers 2
```

**After:**
```bash
# Auto-detect mode (same command for all backends)
python transcribe.py audio.mp3

# Explicit backend selection
python transcribe.py audio.mp3 --backend gpu --speakers 2
python transcribe.py audio.mp3 --backend cpu
python transcribe.py audio.mp3 --backend cloud

# All other options work consistently
python transcribe.py audio.mp3 --language es --no-diarization --verbose
```

---

## 6. Risk Assessment & Mitigation

### 6.1 Risk Matrix

```
Risk Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk ID | Impact | Probability | Mitigation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R1: Performance Regression
────────────────────────────────────────────────────────────
Impact:      HIGH    | New unified pipeline slower than originals
Probability: MEDIUM  | Abstraction overhead could add latency

Mitigation:
✓ Benchmark early and often (Phase 2+)
✓ Profile hot paths with cProfile/line_profiler
✓ Set performance gates in CI (max 5% regression)
✓ Use zero-cost abstractions (avoid runtime overhead)
✓ Keep backends as thin wrappers around existing code

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R2: Breaking Changes for Existing Users
────────────────────────────────────────────────────────────
Impact:      HIGH    | Backend integration breaks
Probability: LOW     | We control the backend

Mitigation:
✓ Maintain backward compatibility shims (Phase 4)
✓ Deprecation warnings, not immediate removal
✓ Comprehensive migration guide
✓ Version bump to 2.0 (signals major changes)
✓ Coordinate with backend team before migration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R3: Feature Parity Gaps
────────────────────────────────────────────────────────────
Impact:      MEDIUM  | Some features lost in consolidation
Probability: MEDIUM  | Easy to miss edge cases

Mitigation:
✓ Feature inventory checklist (all 4 pipelines)
✓ Regression tests for every feature
✓ Side-by-side comparison testing
✓ User acceptance testing with real workloads
✓ Document any intentional removals

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R4: Increased Complexity
────────────────────────────────────────────────────────────
Impact:      LOW     | Abstraction makes code harder to understand
Probability: MEDIUM  | More files, more indirection

Mitigation:
✓ Clear documentation with examples
✓ Architecture diagrams (this document)
✓ Inline comments explaining design decisions
✓ Keep interfaces simple (few methods)
✓ Comprehensive API reference

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R5: GPU Availability Issues
────────────────────────────────────────────────────────────
Impact:      MEDIUM  | GPU backend selected but GPU not available
Probability: LOW     | Detection logic handles this

Mitigation:
✓ Robust GPU detection (torch.cuda.is_available())
✓ Graceful fallback to CPU/cloud
✓ Clear error messages if GPU required but missing
✓ Test on systems without GPU
✓ Document GPU requirements clearly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R6: Dependency Hell
────────────────────────────────────────────────────────────
Impact:      MEDIUM  | Conflicting dependencies across backends
Probability: LOW     | All backends already coexist

Mitigation:
✓ Requirements already unified (requirements.txt)
✓ Optional dependencies for GPU (requirements-gpu.txt)
✓ Test with clean virtual environments
✓ Pin dependency versions
✓ Docker containers for reproducibility

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R7: Testing Gaps
────────────────────────────────────────────────────────────
Impact:      HIGH    | Bugs slip through due to incomplete tests
Probability: MEDIUM  | Many code paths to cover

Mitigation:
✓ Target >90% code coverage
✓ Test all backend combinations
✓ Integration tests with real audio
✓ CI/CD pipeline with automated testing
✓ Manual QA testing before release

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.2 Rollback Plan

**If migration fails, we can rollback safely:**

1. **Phase 1-3**: No impact on existing code (new files only)
   - Simply delete new src/ directory
   - No rollback needed

2. **Phase 4**: Backward compatibility shims in place
   - Old code continues working
   - Remove shims, revert to old files

3. **Phase 5+**: If issues found during testing
   - Keep old files as fallback
   - Document known issues
   - Fix in place or rollback

**Rollback Criteria:**
- Performance regression >10%
- Critical feature missing
- >3 high-severity bugs found
- Backend integration breaks

**Rollback Process:**
```bash
# 1. Revert to pre-migration state
git revert <migration-commit-range>

# 2. Restore old files
git checkout main -- pipeline.py pipeline_gpu.py pipeline_enhanced.py

# 3. Remove new directory
rm -rf src/

# 4. Run old test suite
pytest tests/test_full_pipeline.py

# 5. Communicate to users
echo "Migration rolled back due to <reason>. Using previous version."
```

---

## 7. Success Criteria

### 7.1 Quantitative Metrics

```
Success Metrics (Must Achieve)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Code Quality:
✓ Reduce total LOC by >50% (1,709 → <850)
✓ Reduce duplication by >70% (measured by pylint)
✓ Test coverage >90%
✓ Zero critical or high-severity bugs
✓ Pylint score >9.0/10

Performance:
✓ No regression >5% on any backend
✓ GPU backend: ≥10x real-time transcription
✓ API backend: <2min for 10min audio
✓ Memory usage: <8GB peak (GPU backend)

Maintainability:
✓ Single place to add new features (not 4 places)
✓ Backend addition: <200 LOC (new backend)
✓ Bug fix time: <1hr (vs. 4hrs for 4 files)
✓ New contributor onboarding: <1 day

Compatibility:
✓ All existing tests pass with new implementation
✓ Backend API integration works without changes
✓ Old import paths work with deprecation warnings
✓ CLI backwards compatible (old flags work)
```

### 7.2 Qualitative Goals

```
User Experience:
✓ Simpler mental model (1 pipeline vs. 4)
✓ Easier to switch backends (config change vs. code rewrite)
✓ Better error messages (centralized handling)
✓ Clearer documentation

Developer Experience:
✓ Easier to understand codebase
✓ Faster to implement new features
✓ Less time spent on maintenance
✓ More confidence in changes (better tests)

Architecture:
✓ Clear separation of concerns
✓ Pluggable components (easy to extend)
✓ Consistent interfaces
✓ Well-documented design
```

---

## 8. Open Questions & Decisions Needed

### 8.1 Configuration Format

**Question:** How should users provide configuration?

**Options:**
1. Python API only (PipelineConfig class)
2. YAML/TOML config files
3. Environment variables only
4. All of the above

**Recommendation:** Start with option 1 (Python API) + environment variables. Add YAML support later if needed.

**Rationale:**
- Simpler to implement initially
- Covers 90% of use cases
- Can add config files in future without breaking changes

### 8.2 Backend Naming

**Question:** What should backends be called?

**Options:**
1. "cpu", "gpu", "cloud"
2. "local-cpu", "local-gpu", "api"
3. "pydub", "torch", "openai"

**Recommendation:** Option 1 ("cpu", "gpu", "cloud")

**Rationale:**
- User-centric naming (what resources they have)
- Simple and memorable
- Matches industry conventions

### 8.3 Diarization Label Mapping

**Question:** Should we map generic speaker labels to domain-specific ones?

**Current:** SPEAKER_00, SPEAKER_01 (generic)
**Desired:** Therapist, Client (domain-specific)

**Options:**
1. Keep generic labels (SPEAKER_00/01)
2. Add optional label mapping in post-processing
3. Make label mapping configurable
4. Use ML to auto-detect roles

**Recommendation:** Option 2 (optional post-processing)

**Rationale:**
- Generic labels work for all domains (not just therapy)
- Mapping logic is simple (duration-based heuristic)
- Can be added as separate utility function
- Doesn't complicate core pipeline

**Implementation sketch:**
```python
def map_therapy_roles(segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
    """
    Map generic speaker labels to Therapist/Client based on speaking time.

    Heuristic: Speaker with more total speaking time = Therapist
    """
    # Calculate total speaking time per speaker
    speaker_durations = {}
    for seg in segments:
        if seg.speaker:
            duration = seg.end - seg.start
            speaker_durations[seg.speaker] = speaker_durations.get(seg.speaker, 0) + duration

    # Sort by duration (descending)
    sorted_speakers = sorted(speaker_durations.items(), key=lambda x: x[1], reverse=True)

    # Map to roles
    role_map = {
        sorted_speakers[0][0]: "Therapist",
        sorted_speakers[1][0]: "Client" if len(sorted_speakers) > 1 else "Unknown"
    }

    # Apply mapping
    return [
        TranscriptionSegment(
            start=seg.start,
            end=seg.end,
            text=seg.text,
            speaker=role_map.get(seg.speaker, seg.speaker)
        )
        for seg in segments
    ]
```

### 8.4 Performance Logging

**Question:** Should performance logging be always-on or opt-in?

**Options:**
1. Always-on (minimal overhead)
2. Opt-in via config flag
3. Separate "debug" mode

**Recommendation:** Option 2 (opt-in via config)

**Rationale:**
- Zero overhead when disabled
- Users can enable for debugging
- Keeps implementation simple
- Matches current pipeline_enhanced.py behavior

### 8.5 Model Caching

**Question:** Where should models be cached?

**Current behavior:**
- Colab: /content/models
- Vast.ai: /workspace/models
- Local: ~/.cache/huggingface

**Options:**
1. Keep provider-specific paths
2. Standardize on ~/.cache/audio-pipeline
3. Make fully configurable

**Recommendation:** Option 1 (keep provider-specific) + option 3 (allow override)

**Rationale:**
- Provider-specific paths are optimized for those platforms
- Users can override if needed (via config)
- Auto-detection already works well (gpu_config.py)

---

## 9. Next Steps

### 9.1 Immediate Actions

1. **Review this design document** with team/stakeholders
   - Get feedback on proposed architecture
   - Validate use cases covered
   - Confirm success criteria

2. **Create implementation issues** in GitHub
   - One issue per phase
   - Detailed task breakdown
   - Assign owners

3. **Set up development environment**
   - Create feature branch (feature/unified-pipeline)
   - Set up CI/CD pipeline
   - Configure test environments (CPU + GPU)

### 9.2 Phase 1 Kickoff Checklist

```
Phase 1 Preparation (Week 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Design document approved
□ GitHub project board created
□ Feature branch created (feature/unified-pipeline)
□ Test environments provisioned
  □ CPU-only environment (GitHub Actions)
  □ GPU environment (self-hosted runner or Vast.ai)
□ Development dependencies installed
  □ pytest, pytest-cov
  □ pylint, black, mypy
  □ sphinx (for API docs)
□ Initial file structure created
  □ src/ directory
  □ src/backends/ subdirectories
  □ tests/ reorganization
□ Team kickoff meeting scheduled
```

### 9.3 Go/No-Go Decision Points

**After each phase, assess:**

1. **Are we on track?** (schedule, scope, quality)
2. **Any blockers?** (technical issues, resource constraints)
3. **Should we continue?** (risk assessment, ROI)

**Decision Gate Criteria:**

| Phase | Go Criteria | No-Go Triggers |
|-------|-------------|----------------|
| 1 → 2 | - Interfaces defined<br>- Tests written<br>- Documentation complete | - Fundamental design flaw found<br>- Team bandwidth insufficient |
| 2 → 3 | - All backends pass tests<br>- Performance matches originals | - Feature parity gaps found<br>- Performance regression >10% |
| 3 → 4 | - Integration tests pass<br>- End-to-end tests pass | - Critical bugs found<br>- Architecture needs redesign |
| 4 → 5 | - Backward compatibility verified<br>- Migration guide complete | - Breaking changes for backend<br>- User confusion in testing |
| 5 → 6 | - Test coverage >90%<br>- No high-severity bugs | - Regression tests failing<br>- Performance issues unresolved |

---

## 10. Appendix

### 10.1 Glossary

**Terms used in this document:**

- **Backend**: Execution mode (CPU, GPU, or Cloud/API)
- **Pipeline**: Complete audio transcription workflow
- **Preprocessor**: Audio normalization and format conversion
- **Transcriber**: Speech-to-text conversion
- **Diarizer**: Speaker identification and segmentation
- **Alignment**: Matching text segments with speakers
- **Shim**: Backward compatibility wrapper
- **Contract**: Interface specification (abstract base class)

### 10.2 References

**Existing codebase:**
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline.py`
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline_gpu.py`
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline_enhanced.py`
- `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/src/pipeline_colab.py`

**Dependencies:**
- OpenAI Whisper API: https://platform.openai.com/docs/guides/speech-to-text
- faster-whisper: https://github.com/guillaumekln/faster-whisper
- pyannote.audio: https://github.com/pyannote/pyannote-audio
- pydub: https://github.com/jiaaro/pydub

**Design patterns:**
- Strategy Pattern (backend selection)
- Abstract Factory (component creation)
- Facade Pattern (unified pipeline API)
- Template Method (preprocessing steps)

### 10.3 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-17 | Claude | Initial design document |

---

## Document Status: DRAFT - AWAITING REVIEW

**Next Review Date:** TBD
**Approval Required From:** Project Lead, Backend Team Lead
**Implementation Start Date:** TBD (after approval)

---

*This design document serves as the blueprint for the audio transcription pipeline consolidation. All implementation work should reference this document and update it as decisions are made or architecture evolves.*
