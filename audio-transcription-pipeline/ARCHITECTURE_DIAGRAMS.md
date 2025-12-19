# Audio Transcription Pipeline - Architecture Diagrams

## Component Interaction Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUDIO TRANSCRIPTION PIPELINE                             │
│                        (Two Distinct Paths)                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                              INPUT AUDIO
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  AudioPreprocessor       │
                    │  (CPU: pydub/torchaudio)│
                    │                          │
                    │ • Load audio (any fmt)   │
                    │ • Trim silence           │
                    │ • Normalize (-20dBFS)    │
                    │ • Convert 16kHz mono     │
                    │ • Validate size (<25MB)  │
                    └──────────────┬───────────┘
                                  │
                    Preprocessed audio (MP3/WAV)
                                  │
                    ┌─────────────┴──────────────┐
                    │                            │
                    ▼                            ▼
         ┌──────────────────────┐    ┌──────────────────────┐
         │  CPU/API PATH        │    │  GPU PATH            │
         │  (OpenAI Whisper)    │    │  (Local GPU)         │
         └──────────┬───────────┘    └──────────┬───────────┘
                    │                           │
                    ▼                           ▼
         ┌──────────────────────┐    ┌──────────────────────┐
         │WhisperTranscriber    │    │GPUTranscriptionPipeline
         │(API + Retry Logic)   │    │• GPU Audio Ops       │
         │                      │    │• faster-whisper      │
         │• Exponential backoff │    │• pyannote diarization│
         │• Rate limiting       │    │• Speaker alignment   │
         │• 5x retry max        │    │• GPU monitoring      │
         └──────────┬───────────┘    └──────────┬───────────┘
                    │                           │
                    ├─────────┬─────────────────┤
                    │         │                 │
                    ▼         ▼                 ▼
           Transcription  Speaker Turns    Aligned Segments
           {segments[],   [{speaker,      [{start, end,
            full_text,     start, end}]    text, speaker}]
            language,
            duration}

                              OUTPUT: JSON
                    {segments[], full_text, language,
                     duration, speaker_turns, 
                     aligned_segments, performance_metrics}
```

---

## CPU/API Path Detail

```
OPENAI_API_KEY
     │
     ▼
┌────────────────────────────────────────┐
│         WhisperTranscriber             │
│  (OpenAI Whisper API Client)           │
└────────────┬─────────────────────────┘
             │
             ├─────────────────────────────────────┐
             │                                     │
        Request                              Response
        (audio, lang,                    {segments,
         response_format)                  text,
                                          language,
                                          duration}
             │                                │
             ▼                                ▼
        [OpenAI API]                  [Parse Response]
        • Upload file                  • Extract segments
        • Call whisper-1               • Parse timestamps
        • Handle 429 rate limits       • Join text
        • Exponential backoff
        • Timeout handling


Retry Logic (tenacity):
┌────────────────────────────────────────┐
│        Retry Decision Tree              │
├────────────────────────────────────────┤
│ Error Type          │ Action            │
├─────────────────────┼──────────────────┤
│ RateLimitError(429) │ Backoff + Retry   │
│ APIError            │ Backoff + Retry   │
│ ConnectionError     │ Backoff + Retry   │
│ TimeoutError        │ Backoff + Retry   │
│ Other errors        │ Propagate         │
├────────────────────────────────────────┤
│ Max Retries: 5                          │
│ Backoff: 1s → 60s exponential           │
│ Rate Limit: 0.5s between calls          │
└────────────────────────────────────────┘
```

---

## GPU Path Detail

```
┌─────────────────────────────────────────────────────────────────┐
│           GPUTranscriptionPipeline (Context Manager)            │
│                                                                  │
│  __enter__() → Returns self for 'with' block                   │
│  __exit__()  → Guarantees cleanup even on exception            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │  GPU Provider Auto-Detection    │
        │  (gpu_config.py)                │
        ├─────────────────────────────────┤
        │ Check environment:              │
        │ • /content + COLAB_GPU         │ → Colab
        │ • VAST_CONTAINERLABEL          │ → Vast.ai
        │ • RUNPOD_POD_ID                │ → RunPod
        │ • PAPERSPACE_METRIC_URL        │ → Paperspace
        │ • hostname patterns            │ → Lambda/local
        │                                 │
        │ Optimize:                       │
        │ • Detect GPU model              │
        │ • Query VRAM                    │
        │ • Select compute type           │
        │ • Set cache directory           │
        └──────────┬────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  Stage 1: GPU Audio Preprocessing    │
    │  (GPUAudioProcessor)                 │
    ├──────────────────────────────────────┤
    │ • Load audio → GPU tensors           │
    │ • Trim silence (GPU convolution)     │
    │ • Normalize (GPU peak detection)     │
    │ • Resample 16kHz (julius sinc)       │
    │ • Save preprocessed audio            │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Stage 2: GPU Transcription          │
    │  (faster-whisper)                    │
    ├──────────────────────────────────────┤
    │ • Load Whisper large-v3 (~6GB VRAM) │
    │ • Inference with VAD filter          │
    │ • Extract segments + timestamps      │
    │ • Delete model (free ~6GB)           │
    │ • torch.cuda.empty_cache()           │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Stage 3: GPU Diarization            │
    │  (pyannote-audio 3.1)                │
    ├──────────────────────────────────────┤
    │ • Load diarization model (~3GB)      │
    │ • Load audio waveform → GPU          │
    │ • Run pyannote pipeline              │
    │ • Extract speaker turns              │
    │ • Extract Annotation (compat layer)  │
    │ • Delete waveform (free ~2GB)        │
    │ • Delete model (free ~3GB)           │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Stage 4: GPU Speaker Alignment      │
    │  (GPU tensor operations)             │
    ├──────────────────────────────────────┤
    │ • Create GPU tensors for timings    │
    │ • Vectorized overlap calculation     │
    │ • Apply 50% threshold                │
    │ • Label segments with speakers       │
    │ • Delete tensors (free < 1GB)        │
    └──────────┬───────────────────────────┘
               │
               ▼ (Finally block)
    ┌──────────────────────────────────────┐
    │  GPU Memory Cleanup                  │
    │  (__exit__ guarantee)                │
    ├──────────────────────────────────────┤
    │ • Delete transcriber reference       │
    │ • Delete diarizer reference          │
    │ • torch.cuda.empty_cache()           │
    │ • Log memory recovery                │
    │ • Always executed, even on error     │
    └──────────────────────────────────────┘
```

---

## Performance Logging Architecture

```
┌─────────────────────────────────────────────────────────┐
│          PerformanceLogger (Hierarchical)               │
│                                                          │
│  Pipeline Level (start → end)                          │
│     │                                                   │
│     ├─ Stage 1 (duration, GPU stats)                   │
│     │    │                                              │
│     │    ├─ Subprocess 1A (duration, memory delta)     │
│     │    ├─ Subprocess 1B (duration, memory delta)     │
│     │    └─ Subprocess 1C (duration, memory delta)     │
│     │                                                   │
│     ├─ Stage 2 (duration, GPU stats)                   │
│     │    │                                              │
│     │    ├─ Subprocess 2A (duration, memory delta)     │
│     │    └─ Subprocess 2B (duration, memory delta)     │
│     │                                                   │
│     └─ Stage 3 (duration, GPU stats)                   │
│          │                                              │
│          └─ Subprocess 3A (duration, memory delta)     │
│                                                          │
│  GPU Monitor (background thread):                      │
│  • Samples every 0.1s                                  │
│  • Tracks utilization %, memory, temperature           │
│  • Aggregates: min, max, avg                           │
│                                                          │
│  Output:                                                │
│  • JSON report: metrics, timings, system info          │
│  • Text report: human-readable breakdown               │
│  • Log buffer: recent log entries                      │
└─────────────────────────────────────────────────────────┘
```

---

## Data Structures

### Pipeline Input/Output

```
INPUT:
  audio_path: str (path to audio file)
  num_speakers: int (for diarization, typically 2)
  language: str (language code, default "en")
  enable_diarization: bool (whether to run speaker ID)

OUTPUT:
{
  "segments": [
    {
      "start": 0.5,           # Segment start time (seconds)
      "end": 2.3,             # Segment end time
      "text": "Hello there",  # Transcribed text
      "speaker": "Speaker 0"  # Only in aligned_segments
    }
  ],
  "full_text": "Hello there how are you",  # Complete transcription
  "language": "en",                       # Detected language
  "duration": 45.6,                       # Total audio duration
  "speaker_turns": [
    {
      "speaker": "Speaker 0",
      "start": 0.0,
      "end": 2.5
    }
  ],
  "aligned_segments": [
    {
      "start": 0.5,
      "end": 2.3,
      "text": "Hello there",
      "speaker": "Speaker 0"
    }
  ],
  "provider": "vast_ai",  # GPU provider
  "performance_metrics": {
    "total_duration": 15.3,
    "stages": {
      "GPU Audio Preprocessing": {
        "duration": 2.1,
        "gpu_stats": {...}
      },
      "GPU Transcription": {
        "duration": 8.5,
        "gpu_stats": {...}
      },
      ...
    }
  }
}
```

---

## Module Dependencies

```
┌────────────────────────────────────────────────────────────┐
│                    Pipeline Variants                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  pipeline.py (CPU/API)                                     │
│  ├─ AudioPreprocessor                                     │
│  └─ WhisperTranscriber                                    │
│     ├─ pydub (audio loading)                              │
│     ├─ openai (API client)                                │
│     ├─ tenacity (retry logic)                             │
│     └─ python-dotenv (env vars)                           │
│                                                             │
│  pipeline_gpu.py (GPU)                                     │
│  ├─ GPUTranscriptionPipeline                              │
│  ├─ GPUAudioProcessor                                     │
│  ├─ gpu_config (provider detection)                       │
│  ├─ performance_logger (monitoring)                       │
│  └─ pyannote_compat (version compatibility)               │
│     ├─ torch (GPU operations)                             │
│     ├─ torchaudio (audio loading)                         │
│     ├─ julius (resampling)                                │
│     ├─ faster-whisper (local transcription)               │
│     └─ pyannote.audio (diarization)                       │
│                                                             │
│  pipeline_enhanced.py (CPU with logging)                  │
│  ├─ AudioPreprocessor (with logger)                       │
│  ├─ WhisperTranscriber (with logger)                      │
│  ├─ SpeakerDiarizer                                       │
│  └─ performance_logger (detailed metrics)                 │
│                                                             │
│  youtube_to_transcript.py (End-to-end)                    │
│  ├─ YouTubeSessionDownloader                              │
│  ├─ GPUTranscriptionPipeline                              │
│  └─ (handles download + transcription + diarization)      │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## GPU Memory Timeline

```
Time ──────────────────────────────────────────────────────────>

Init:
  [Free: 24GB] ─────────────────────────────────────────────

Load Whisper:
  [Whisper 6GB][Free: 18GB] ─────────────────────────────────

Transcribe:
  [Whisper 6GB][Audio tensors 1GB][Free: 17GB] ─────────────

Delete Whisper:
  [Free: 24GB] ──────────────────────────────────────────────

Load Diarizer:
  [Diarizer 3GB][Free: 21GB] ────────────────────────────────

Load waveform:
  [Diarizer 3GB][Waveform 2GB][Free: 19GB] ──────────────────

Diarize:
  [Diarizer 3GB][Waveform 2GB][Tensors 1GB][Free: 18GB] ─────

Delete waveform:
  [Diarizer 3GB][Free: 21GB] ────────────────────────────────

Delete Diarizer:
  [Free: 24GB] ──────────────────────────────────────────────

Alignment:
  [Alignment tensors 0.5GB][Free: 23.5GB] ───────────────────

Final cleanup:
  [Free: 24GB] ──────────────────────────────────────────────
```

---

## Error Handling Flow

```
API Call (Whisper)
    │
    ▼
Try API Request
    │
    ├─ Success ──────────────────────> Return result
    │
    └─ Exception
        │
        ├─ RateLimitError (429)
        │   │
        │   ├─ Attempt 1: Wait 1s → Retry
        │   ├─ Attempt 2: Wait 2s → Retry
        │   ├─ Attempt 3: Wait 4s → Retry
        │   ├─ Attempt 4: Wait 8s → Retry
        │   ├─ Attempt 5: Wait 16s → Retry
        │   │
        │   └─ Max retries exceeded ──────> Raise RateLimitError
        │
        ├─ APIConnectionError
        │   └─ Exponential backoff × 5 ──> Raise APIConnectionError
        │
        ├─ APITimeoutError
        │   └─ Exponential backoff × 5 ──> Raise APITimeoutError
        │
        └─ Other Exception
            └──────────────────────────> Raise immediately

GPU Operations
    │
    ├─ OOM (Out of Memory)
    │   │
    │   ├─ Is memory > 85%?
    │   │   └─ Yes: Log CRITICAL warning
    │   │
    │   └─ Exception propagates ──> Caught by finally block
    │
    └─ Model load failure
        └─ Exception propagates ──> Caught by context manager __exit__
```

---

## Quality Assurance Points

```
┌─────────────────────────────────────────┐
│  Input Validation                       │
├─────────────────────────────────────────┤
│ • File exists check                     │
│ • Audio format validation               │
│ • File size < 25MB (API only)           │
│ • Language code validation              │
│ • num_speakers > 0                      │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│  Processing Stages                      │
├─────────────────────────────────────────┤
│ • Stage timing verification             │
│ • GPU memory monitoring                 │
│ • API response validation               │
│ • Model loading success check           │
│ • Diarization output validation         │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│  Output Validation                      │
├─────────────────────────────────────────┤
│ • Segments have valid timestamps        │
│ • Segments sorted chronologically       │
│ • Speaker labels not empty              │
│ • Full text matches segment concatenation
│ • Performance metrics present           │
└─────────────────────────────────────────┘
```

