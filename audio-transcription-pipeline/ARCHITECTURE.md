# Audio Transcription Pipeline - Comprehensive Architecture Analysis

## Executive Summary

The audio-transcription-pipeline is a sophisticated, multi-stage audio processing system designed for converting speech to text with speaker identification. It features two distinct execution paths:
1. **CPU/API path** - Using OpenAI Whisper API (lighter weight, no GPU required)
2. **GPU path** - Local GPU-accelerated transcription with pyannote speaker diarization (high performance)

Both paths maintain the same data flow but with different computational backends.

---

## Core Pipeline Architecture

### Data Flow Overview

```
Raw Audio File
    ↓
[STAGE 1] Audio Preprocessing
    ├─ Load audio (any format via ffmpeg)
    ├─ Trim leading/trailing silence
    ├─ Normalize volume to -20dBFS
    ├─ Convert to mono 16kHz
    └─ Export as MP3/WAV (<25MB for API)
    ↓
[STAGE 2] Transcription
    ├─ API path: OpenAI Whisper API (with retry logic)
    └─ GPU path: faster-whisper local model
    ↓
[STAGE 3] Speaker Diarization (GPU only)
    ├─ Load audio as GPU tensor
    ├─ Run pyannote-audio 3.1 pipeline
    ├─ Extract speaker turns with timestamps
    └─ Align speakers to transcription segments
    ↓
[STAGE 4] Speaker Alignment
    ├─ Match speaker turns to transcript segments
    ├─ Apply 50% overlap threshold
    └─ Label segments with speaker IDs
    ↓
Final Output (JSON)
    ├─ segments: [{start, end, text, speaker}]
    ├─ full_text: complete transcript
    ├─ speaker_turns: raw diarization output
    ├─ language: detected language
    ├─ duration: audio length in seconds
    └─ performance_metrics: timing and GPU stats
```

---

## Core Module Responsibilities

### 1. **pipeline.py** - CPU/API Pipeline (13.2 KB)

**Class: AudioPreprocessor**
- Responsibility: Audio file preparation for transcription
- Key methods:
  - `preprocess(audio_path, output_path)` - Full preprocessing pipeline
  - `_trim_silence(audio, threshold, min_len)` - Remove leading/trailing silence
  - `_normalize(audio, target_dBFS)` - Normalize to -20dBFS with 0.1dB headroom
  - `validate_audio(audio_path)` - Extract audio metadata

- Processing pipeline:
  ```
  Load audio (pydub) 
    → Trim silence (detect_leading_silence)
    → Normalize volume (effects.normalize)
    → Convert to mono (set_channels(1))
    → Resample to 16kHz (set_frame_rate)
    → Export as MP3 (validate < 25MB)
  ```

**Class: WhisperTranscriber**
- Responsibility: OpenAI Whisper API transcription with resilience
- Key features:
  - Exponential backoff retry logic (tenacity library)
  - Rate limiting (0.5s delay between calls)
  - Handles transient failures (429, 5xx errors)
  - Verbose JSON response format (segment-level timestamps)
  
- Retry configuration:
  - Max retries: 5 attempts
  - Min backoff: 1 second
  - Max backoff: 60 seconds
  - Rate limit delay: 0.5 seconds

- Error handling:
  - RateLimitError (429) → Exponential backoff retry
  - APIError, APIConnectionError → Automatic retry
  - APITimeoutError → Exponential backoff
  - File size validation (< 25MB Whisper limit)

- Output structure:
  ```python
  {
    "segments": [{"start": float, "end": float, "text": str}],
    "full_text": str,
    "language": str,
    "duration": float
  }
  ```

**Class: AudioTranscriptionPipeline**
- Responsibility: Orchestrate CPU path stages
- Combines AudioPreprocessor + WhisperTranscriber
- No speaker diarization capability

---

### 2. **pipeline_gpu.py** - GPU-Accelerated Pipeline (24.3 KB)

**Class: GPUTranscriptionPipeline**
- Responsibility: Complete GPU-accelerated transcription with diarization
- Design pattern: Context manager (guarantees cleanup even on exception)

- Initialization:
  - Auto-detects GPU provider (Colab, Vast.ai, RunPod, Lambda, Paperspace, Local)
  - Auto-configures optimal compute type (float16, int8, float32)
  - Initializes performance logger with GPU monitoring
  - Lazy-loads models (transcriber, diarizer) on first use

- Key method: `process(audio_path, num_speakers, language, enable_diarization)`
  - Returns dict with segments, aligned segments, speaker turns, and performance metrics
  
- Four-stage execution:
  1. GPU Audio Preprocessing (`_preprocess_gpu`)
  2. GPU Transcription (`_transcribe_gpu`)
  3. GPU Diarization (`_diarize_gpu`)
  4. Speaker Alignment (`_align_speakers_gpu`)

- Memory management:
  - Cleans up Whisper model after transcription
  - Cleans up diarizer after diarization
  - Tracks GPU tensors and frees them explicitly
  - Logs GPU memory at each stage for OOM monitoring
  - Context manager ensures cleanup even on exception

- Output structure (same as CPU path + aligned segments):
  ```python
  {
    "segments": [{start, end, text}],
    "aligned_segments": [{start, end, text, speaker}],
    "full_text": str,
    "language": str,
    "duration": float,
    "speaker_turns": [{speaker, start, end}],
    "provider": str,
    "performance_metrics": {...}
  }
  ```

---

### 3. **gpu_audio_ops.py** - GPU Audio Operations (7.4 KB)

**Class: GPUAudioProcessor**
- Responsibility: GPU-accelerated audio processing (replaces pydub on GPU)
- Device: NVIDIA GPU via PyTorch (CUDA)
- Design pattern: Context manager for cleanup

- Key operations:
  - `load_audio(path)` - Load to GPU via torchaudio
  - `resample_gpu(waveform, orig_sr, target_sr)` - High-quality sinc resampling via julius library
  - `trim_silence_gpu(waveform, threshold, min_duration, sr)` - GPU-accelerated silence detection
  - `normalize_gpu(waveform, target_db, headroom)` - Peak normalization on GPU
  - `detect_silence_gpu(waveform, threshold, min_duration, sr)` - GPU tensor operations
  - `save_audio_gpu(waveform, sr, output_path, format)` - Save tensor to disk

- Silence detection algorithm:
  ```
  Calculate dB levels: 20 * log10(|audio| + 1e-10)
  Create silence mask: dB_levels < threshold_db
  Apply morphological ops: 1D convolution for region detection
  Return: silence regions
  ```

- Memory cleanup:
  - Moves tensors to CPU before saving
  - Deletes waveform tensors after use
  - Calls torch.cuda.empty_cache() for explicit cache clearing

---

### 4. **gpu_config.py** - GPU Provider Detection (6.9 KB)

**Class: GPUConfig**
- Data class holding GPU configuration parameters
- Fields: provider, device_name, vram_gb, compute_type, batch_size, num_workers, enable_tf32, model_cache_dir

**Functions: Provider Detection**
- `detect_provider()` - Auto-detects GPU provider from environment variables and filesystem
  - Checks: `/content` + COLAB_GPU env var → Google Colab
  - Checks: VAST_CONTAINERLABEL or VAST_CONTAINER_USER → Vast.ai
  - Checks: RUNPOD_POD_ID → RunPod
  - Checks: PAPERSPACE_METRIC_URL or `/storage` → Paperspace
  - Fallback: hostname pattern matching
  - Default: LOCAL or UNKNOWN

- `get_optimal_config()` - Auto-configures based on detected GPU
  - Validates CUDA availability (detailed error messages if not)
  - Queries GPU properties:
    - Device name
    - Total VRAM
    - Compute capability
  - Selects compute type:
    - A100/H100 → float16
    - RTX 3090/4090/A6000 → int8
    - Others → int8 (safe default)
  - Sets model cache directory based on provider:
    - Colab: `/content/models`
    - Vast.ai/RunPod: `/workspace/models`
    - Paperspace: `/storage/models`
    - Local: `~/.cache/huggingface`
  - Enables TF32 optimization on high-end GPUs

---

### 5. **performance_logger.py** - Performance Monitoring (18.8 KB)

**Class: PerformanceLogger**
- Responsibility: Hierarchical performance tracking across entire pipeline
- Features:
  - Stage-level timing tracking
  - Subprocess-level timing with metadata
  - GPU utilization monitoring (background thread)
  - Memory tracking (psutil)
  - Dual output: JSON + human-readable text reports

- Data structure:
  ```python
  metrics = {
    "start_time": float,
    "end_time": float,
    "total_duration": float,
    "stages": {
      "stage_name": {
        "duration": float,
        "subprocesses": {...},
        "gpu_stats": {...}
      }
    },
    "subprocesses": {
      "name": [{"duration": float, "metadata": {}}]
    },
    "gpu_stats": {},
    "memory_stats": {}
  }
  ```

- Key methods:
  - `start_pipeline()` / `end_pipeline()` - Mark pipeline boundaries
  - `start_stage(name)` / `end_stage(name)` - Track major stages
  - `subprocess(name, metadata)` - Context manager for subprocess timing
  - `timer(name)` - Simple context manager for arbitrary code blocks
  - `generate_reports()` - Create JSON + text performance reports
  - `log(message, level)` - Timestamped logging

**Class: GPUMonitor**
- Responsibility: Background GPU monitoring during execution
- Thread-based monitoring at 0.1s intervals
- Tracks:
  - GPU utilization percentage
  - Memory allocated/reserved
  - GPU temperature (via GPUtil)
- Returns aggregated statistics (avg, max)

**Class: PerformanceTimer**
- Simple context manager for timing code blocks
- Automatically logs to PerformanceLogger

---

### 6. **pyannote_compat.py** - Version Compatibility (3.98 KB)

**Responsibility**: Handle pyannote.audio version differences (3.x vs 4.x)

**Key functions:**
- `get_pyannote_version()` - Parse installed pyannote.audio version
- `extract_annotation(diarization_result)` - Transparently extract Annotation from different output types
  - pyannote 3.x: Returns Annotation directly
  - pyannote 4.x: Returns DiarizeOutput with speaker_diarization or exclusive_speaker_diarization
  - Prefers exclusive (cleaner, no overlapping speech)

- `log_version_info(logger_func)` - Diagnostic logging of pyannote version

---

### 7. **pipeline_enhanced.py** - Enhanced CPU Pipeline (26.1 KB)

**Responsibility**: CPU path with comprehensive performance logging

- Wraps AudioPreprocessor, WhisperTranscriber, and SpeakerDiarizer
- Each stage integrates with PerformanceLogger
- Provides subprocess-level timing for:
  - Audio loading, silence trimming, normalization, format conversion, export
  - Whisper file preparation, API call, response parsing
  - Diarization model loading, inference, annotation extraction
  - Speaker alignment with GPU acceleration (if available)

**Class: SpeakerDiarizer**
- CPU-based diarization using pyannote-audio (requires HF_TOKEN)
- Less efficient than GPU path but functional on CPU

**Class: EnhancedAudioTranscriptionPipeline**
- Orchestrates full pipeline with performance tracking
- Supports both CPU and GPU speaker alignment
- Generates detailed performance reports

---

### 8. **youtube_to_transcript.py** - YouTube Integration (15.1 KB)

**Class: YouTubeTranscriptPipeline**
- Responsibility: Complete end-to-end pipeline (download → transcribe → diarize)
- Combines YouTubeSessionDownloader + GPUTranscriptionPipeline
- Methods:
  - `process_url(url, num_speakers, enable_diarization)` - Full pipeline
  - `process_batch(urls, output_csv)` - Batch processing

---

## Integration Points

### 1. External Dependencies

**Core Libraries:**
- **pydub** - CPU audio processing (loading, resampling, normalization)
- **torchaudio** - GPU audio loading (efficient GPU tensor loading)
- **julius** - GPU audio resampling (sinc interpolation)
- **torch/PyTorch** - GPU tensor operations
- **faster-whisper** - Local GPU Whisper transcription (optimized C++ backend)
- **pyannote.audio** - GPU speaker diarization (CNN with speech/silence detection)
- **openai** - OpenAI API client
- **tenacity** - Exponential backoff retry logic
- **python-dotenv** - Environment variable loading

**External Services:**
- **OpenAI Whisper API** - Cloud-based transcription (CPU path)
- **HuggingFace Hub** - Model downloads (pyannote, HF_TOKEN required)

**System Requirements:**
- **ffmpeg** - Audio codec support (used by pydub)
- **CUDA Toolkit 11.8+** - GPU support (for GPU path)
- **NVIDIA GPU** - VRAM (8GB+ recommended for large models)

### 2. API Integrations

**OpenAI Whisper API (CPU path)**
```
POST /v1/audio/transcriptions
├─ model: "whisper-1"
├─ file: audio file (< 25MB)
├─ language: "en"
├─ response_format: "verbose_json" (for segments with timestamps)
└─ timestamp_granularities: ["segment"]

Response:
├─ text: full transcription
├─ language: detected language
├─ duration: audio duration
└─ segments: [{start, end, text}]
```

**HuggingFace Models (GPU path)**
```
Pipeline.from_pretrained(
  "pyannote/speaker-diarization-3.1",
  token=HF_TOKEN,
  cache_dir=model_cache_dir
)

Input: {waveform, sample_rate}
Output: Annotation or DiarizeOutput (version-dependent)
```

### 3. Data Flow Between Components

```
AudioPreprocessor
├─ Input: audio_path (any format)
├─ Output: processed_audio.mp3/wav (16kHz mono)
└─ Used by: WhisperTranscriber, GPUAudioProcessor

WhisperTranscriber
├─ Input: processed_audio + language code
├─ Output: {segments[], full_text, language, duration}
└─ Used by: AudioTranscriptionPipeline, YouTubeTranscriptPipeline

GPUAudioProcessor
├─ Input: audio_path
├─ Output: GPU tensors (waveform, sample_rate)
└─ Used by: GPUTranscriptionPipeline (diarization)

GPUTranscriptionPipeline
├─ Input 1: audio_path (from preprocessing)
├─ Input 2: num_speakers (for diarization)
├─ Output 1: transcription {segments[], full_text, language, duration}
├─ Output 2: speaker_turns [{speaker, start, end}]
├─ Output 3: aligned_segments [{start, end, text, speaker}]
└─ Used by: YouTubeTranscriptPipeline, Backend API

PerformanceLogger
├─ Monitors: All stages and subprocesses
├─ Output: performance_metrics, JSON/text reports
└─ Used by: All pipeline variants
```

---

## Error Handling Strategy

### 1. API Resilience (OpenAI Whisper)

**Retry Pattern (tenacity library):**
- Stop condition: 5 attempts maximum
- Wait strategy: Exponential backoff (1s min, 60s max)
- Retryable errors:
  - RateLimitError (429) → HTTP rate limit
  - APIError → Generic API errors
  - APIConnectionError → Network issues
  - APITimeoutError → Timeout
- Non-retryable: All other exceptions propagate

**Rate limiting:**
- Manual delay before each API call (0.5s)
- Tracks last_api_call_time for enforcement

### 2. GPU Memory Management

**Prevention:**
- Track GPU memory at each stage
- Warning at 70% utilization, critical at 85%
- Suggests batch size reduction if critical

**Recovery:**
- Explicit tensor deletion (del tensor)
- torch.cuda.empty_cache() after model cleanup
- Finally blocks ensure cleanup even on exception
- Context manager pattern guarantees cleanup

**Staged cleanup:**
1. Delete Whisper model after transcription (free ~6GB)
2. Delete waveform tensor after diarization (free ~2GB)
3. Delete alignment tensors (free < 1GB)
4. Empty cache and log recovered memory

### 3. File Validation

**Audio preprocessing:**
- Validate audio file exists
- Check file size < 25MB (Whisper API limit)
- Detect and reject invalid formats
- Return detailed validation metadata

**File size limits:**
- Whisper API: 25MB maximum
- Enforced during preprocessing
- Error message suggests compression or chunking

### 4. Configuration Errors

**GPU detection failures:**
- Detailed error if CUDA not available
- Suggests CUDA installation steps
- Fallback: Use CPU pipeline instead
- Provides diagnostic command

**Environment variable errors:**
- OPENAI_API_KEY missing → ValueError with instruction
- HF_TOKEN missing → ValueError with HF link
- Early failure with clear diagnostic

---

## Performance Characteristics

### 1. Transcription Speed

**CPU/API path (pipeline.py):**
- Preprocessing: ~5-10 seconds (depends on duration)
- API transcription: ~10-60 seconds (network dependent)
- Total: ~15-70 seconds for 1-hour audio

**GPU path (pipeline_gpu.py):**
- Preprocessing: ~2-5 seconds (GPU accelerated)
- Transcription: ~5-20 seconds (faster-whisper optimized)
- Diarization: ~10-30 seconds (depends on num_speakers)
- Alignment: ~1-2 seconds (GPU tensor operations)
- Total: ~18-57 seconds for 1-hour audio (5-20x real-time)

### 2. GPU Memory Usage

**Model loading:**
- Whisper large-v3: ~6-8 GB VRAM
- Pyannote-audio 3.1: ~2-3 GB VRAM
- Audio tensors: ~1-2 GB (depends on duration)
- Alignment tensors: < 0.5 GB

**Total requirement:** ~10-14 GB for large models
- Minimum: 8GB (small/medium models)
- Recommended: 16GB+ (safety margin)

### 3. CPU Path Advantages

- No GPU required (laptop, CPU-only servers)
- Lower infrastructure cost
- Smaller code footprint
- Reliable (OpenAI maintains API)

### 4. GPU Path Advantages

- 5-20x faster on 1-hour+ audio
- Local processing (data privacy)
- No API rate limits
- Can process longer audio (API is 25MB limit)
- Real-time speaker identification

---

## Configuration & Environment

### 1. Required Environment Variables

```bash
# Required for all paths
OPENAI_API_KEY=sk-...  # Or comment out if using GPU path only

# Required for GPU diarization
HF_TOKEN=hf_...        # Get from https://huggingface.co/settings/tokens

# Optional
TRANSFORMERS_CACHE=/path/to/cache  # Model cache (auto-set by gpu_config)
HF_HOME=/path/to/hf                # HuggingFace home (auto-set by gpu_config)
```

### 2. GPU Provider Customization

Auto-detected, but can be overridden:

```python
from gpu_config import GPUConfig, GPUProvider

config = GPUConfig(
  provider=GPUProvider.VASTAI,
  device_name="RTX 4090",
  vram_gb=24,
  compute_type="float16",
  batch_size=8,
  num_workers=4,
  enable_tf32=True,
  model_cache_dir="/workspace/models"
)

pipeline = GPUTranscriptionPipeline(config=config)
```

### 3. Model Selection

```python
# CPU/API path (no choice needed)
pipeline = AudioTranscriptionPipeline()

# GPU path (specify Whisper model)
with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    # Options: "tiny", "base", "small", "medium", "large-v3"
    result = pipeline.process(audio_file)
```

---

## Usage Examples

### Example 1: Simple CPU/API Transcription

```python
from src.pipeline import AudioTranscriptionPipeline

pipeline = AudioTranscriptionPipeline()
result = pipeline.process("meeting.mp3")

print(f"Transcription: {result['full_text']}")
print(f"Duration: {result['duration']}s")
print(f"Segments: {len(result['segments'])}")
```

### Example 2: GPU Transcription with Diarization

```python
from src.pipeline_gpu import GPUTranscriptionPipeline

with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    result = pipeline.process(
        "therapy_session.mp3",
        num_speakers=2,
        enable_diarization=True
    )

for seg in result['aligned_segments']:
    print(f"[{seg['speaker']}] {seg['text']}")
```

### Example 3: YouTube Session Download + Transcription

```python
from src.youtube_to_transcript import YouTubeTranscriptPipeline

pipeline = YouTubeTranscriptPipeline(whisper_model="large-v3")
result = pipeline.process_url(
    "https://youtube.com/watch?v=...",
    num_speakers=2,
    enable_diarization=True
)

print(f"Downloaded: {result['download_info']['title']}")
print(f"Transcribed: {len(result['segments'])} segments")
print(f"Processing time: {result['performance_metrics']['total_duration']:.1f}s")
```

### Example 4: Batch Processing with Performance Tracking

```python
from src.pipeline_enhanced import EnhancedAudioTranscriptionPipeline

pipeline = EnhancedAudioTranscriptionPipeline(
    enable_performance_logging=True,
    output_dir="outputs"
)

files = ["audio1.mp3", "audio2.wav", "audio3.m4a"]
for audio_file in files:
    result = pipeline.process(audio_file, enable_diarization=True)
    print(f"Processed {audio_file} in {result['performance_metrics']['total_duration']:.1f}s")
```

---

## Key Design Patterns

### 1. Context Manager Pattern (GPU safety)
```python
with GPUTranscriptionPipeline() as pipeline:
    result = pipeline.process(audio_file)
    # Guaranteed cleanup even if exception occurs
```

### 2. Lazy Model Loading
- Whisper model only loaded on first transcription call
- Pyannote model only loaded if diarization enabled
- Models deleted after use to free GPU memory

### 3. Provider Auto-Detection
- Detects execution environment (Colab, Vast.ai, etc.)
- Configures cache directory appropriately
- Adjusts compute type based on GPU model

### 4. Hierarchical Performance Tracking
```python
Logger
├─ Pipeline level (total duration)
├─ Stage level (preprocessing, transcription, etc.)
└─ Subprocess level (detailed operations)
```

### 5. Exponential Backoff with Rate Limiting
- Automatic retry for transient API failures
- Manual rate limiting for API quotas
- Detailed logging of retry attempts

### 6. GPU Memory Profiling
- Logs memory state at each stage
- Warns at 70%, critical at 85%
- Tracks memory recovery after cleanup

---

## Data Processing Pipeline Summary

| Stage | CPU/API | GPU | Input | Output | Failure Modes |
|-------|---------|-----|-------|--------|---------------|
| Preprocess | pydub | pytorch | raw audio | 16kHz mono | invalid format, size > 25MB |
| Transcribe | OpenAI API | faster-whisper | preprocessed | segments[] | API rate limit, timeout, invalid API key |
| Diarize | pyannote (CPU) | pyannote (GPU) | audio tensor | speaker turns | HF_TOKEN missing, no GPU |
| Align | CPU tensors | GPU tensors | segments + turns | labeled segments | no speakers detected |

---

## Monitoring & Observability

### Performance Metrics Generated

1. **Stage timings**: Duration of each major stage
2. **Subprocess timings**: Individual operation durations
3. **GPU stats**: Utilization %, memory usage, temperature
4. **Memory stats**: Peak usage, delta per subprocess
5. **Audio metadata**: Duration, channels, sample rate, file size

### Output Files

```
outputs/performance_logs/
├─ performance_YYYYMMDD_HHMMSS.json    # Machine-readable metrics
├─ performance_YYYYMMDD_HHMMSS.txt     # Human-readable report
└─ transcription_result.json            # Final transcription output
```

### Health Checks

- CPU path: Verify OPENAI_API_KEY is set
- GPU path: Verify torch.cuda.is_available() == True
- Diarization: Verify HF_TOKEN is set
- Audio: Validate format and size before processing

