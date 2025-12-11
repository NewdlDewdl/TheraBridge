# Google Colab L4 GPU Pipeline - Setup & Troubleshooting Log

> **Last Updated**: 2025-12-10
> **Status**: IN PROGRESS - `torchaudio.AudioMetaData` error unresolved
> **Environment**: Google Colab L4 GPU, CUDA 12.1, cuDNN 8.x

---

## Table of Contents

- [Goal](#goal)
- [Environment Summary](#environment-summary)
- [Quick Start (Current Best Attempt)](#quick-start-current-best-attempt)
- [Error Log](#error-log)
- [Dependency Compatibility Matrix](#dependency-compatibility-matrix)
- [Key Learnings](#key-learnings)
- [Next Steps](#next-steps)
- [References](#references)

---

## Goal

Speed up audio transcription pipeline using Google Colab L4 GPU with:
- **faster-whisper** (CTranslate2-based Whisper) for transcription
- **pyannote.audio** for speaker diarization
- Target: 10-15x realtime processing for 52-min audio files

---

## Environment Summary

### Google Colab L4 GPU (as of Dec 2025)

| Component | Version | Notes |
|-----------|---------|-------|
| GPU | NVIDIA L4 | 24GB VRAM |
| CUDA | 12.1 | Pre-installed |
| cuDNN | 8.x (8.7.0.84) | **NOT 9.x** - critical constraint |
| Python | 3.12 | Pre-installed |
| PyTorch | 2.5.0+cu121 | Pre-installed, uses cuDNN 8.x |
| torchaudio | 2.5.0+cu121 | Pre-installed |

### Target Stack

| Package | Required Version | Constraint Reason |
|---------|-----------------|-------------------|
| ctranslate2 | ==4.4.0 | >=4.5.0 requires cuDNN 9.x |
| faster-whisper | latest | Uses ctranslate2 |
| pyannote.audio | ==3.1.1 (testing) | >=3.3.x has torchaudio.AudioMetaData issue |

---

## Quick Start (Current Best Attempt)

### Prerequisites

1. **Factory Reset**: Runtime → Disconnect and delete runtime
2. **Set L4 GPU**: Runtime → Change runtime type → L4
3. **Accept HuggingFace Terms** (REQUIRED):
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

### Cell 1: Install Dependencies

```python
# Install ffmpeg
!apt-get install -y ffmpeg -qq

# Pin ctranslate2 for cuDNN 8.x compatibility
!pip install ctranslate2==4.4.0 -q

# Install faster-whisper
!pip install faster-whisper -q

# Pin pyannote.audio 3.1.1 (attempting to fix AudioMetaData issue)
!pip install pyannote.audio==3.1.1 -q

# Verify
import torch
import ctranslate2
print(f"torch: {torch.__version__}")
print(f"ctranslate2: {ctranslate2.__version__}")
print(f"CUDA: {torch.version.cuda}")
print(f"cuDNN: {torch.backends.cudnn.version()}")
```

### Cell 2: Config & GPU Verification

```python
import torch
import os
from google.colab import files

# Config
HF_TOKEN = "YOUR_HF_TOKEN_HERE"  # Get from huggingface.co/settings/tokens
AUDIO_FILE = "/content/compressed-cbt-session.m4a"
NUM_SPEAKERS = 2
LANGUAGE = "en"
WHISPER_MODEL = "large-v3"
OUTPUT_DIR = "/content/output"

# Verify GPU
if not torch.cuda.is_available():
    raise RuntimeError("CUDA not available! Set runtime to L4 GPU")

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Upload audio if not present
if not os.path.exists(AUDIO_FILE):
    print("\nUpload compressed-cbt-session.m4a:")
    uploaded = files.upload()
    AUDIO_FILE = f"/content/{list(uploaded.keys())[0]}"

print(f"Audio: {AUDIO_FILE}")
```

### Cell 3: Load Models

```python
import time
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

print("Loading Whisper large-v3...")
load_start = time.time()
whisper_model = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
print(f"Whisper loaded in {time.time() - load_start:.1f}s")

print("\nLoading Pyannote diarization...")
load_start = time.time()
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN  # Note: 'token' not 'use_auth_token'
)
diarization_pipeline.to(torch.device("cuda"))
print(f"Pyannote loaded in {time.time() - load_start:.1f}s")
```

### Cell 4: Transcribe

```python
print(f"Transcribing: {AUDIO_FILE}")
start = time.time()

segments_raw, info = whisper_model.transcribe(
    AUDIO_FILE,
    language=LANGUAGE,
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500)
)

transcription_segments = [
    {"start": s.start, "end": s.end, "text": s.text.strip()}
    for s in segments_raw
]

audio_duration = info.duration
transcription_time = time.time() - start

print(f"{len(transcription_segments)} segments in {transcription_time:.1f}s")
print(f"Speed: {audio_duration/transcription_time:.1f}x realtime")
```

### Cell 5: Diarize

```python
import torchaudio

waveform, sample_rate = torchaudio.load(AUDIO_FILE)
waveform = waveform.to("cuda")

print("Running speaker diarization...")
start = time.time()

diarization_result = diarization_pipeline(
    {"waveform": waveform, "sample_rate": sample_rate},
    num_speakers=NUM_SPEAKERS
)

speaker_turns = [
    {"speaker": spk, "start": turn.start, "end": turn.end}
    for turn, _, spk in diarization_result.itertracks(yield_label=True)
]

diarization_time = time.time() - start
print(f"{len(speaker_turns)} speaker turns in {diarization_time:.1f}s")
print(f"Speed: {audio_duration/diarization_time:.1f}x realtime")
```

### Cell 6: Align Speakers

```python
seg_starts = torch.tensor([s["start"] for s in transcription_segments], device="cuda")
seg_ends = torch.tensor([s["end"] for s in transcription_segments], device="cuda")
turn_starts = torch.tensor([t["start"] for t in speaker_turns], device="cuda")
turn_ends = torch.tensor([t["end"] for t in speaker_turns], device="cuda")

overlaps = torch.clamp(
    torch.minimum(seg_ends.unsqueeze(1), turn_ends) -
    torch.maximum(seg_starts.unsqueeze(1), turn_starts),
    min=0
)

max_overlaps, best_idx = torch.max(overlaps, dim=1)
threshold_mask = (max_overlaps / (seg_ends - seg_starts)) >= 0.5

aligned_segments = []
for i, seg in enumerate(transcription_segments):
    speaker = speaker_turns[best_idx[i].item()]["speaker"] if threshold_mask[i] else "UNKNOWN"
    aligned_segments.append({**seg, "speaker": speaker})

print(f"Aligned {len(aligned_segments)} segments with speakers")
```

### Cell 7: Save & Download

```python
import json
from datetime import datetime

os.makedirs(OUTPUT_DIR, exist_ok=True)

result = {
    "metadata": {
        "source_file": AUDIO_FILE,
        "duration_min": audio_duration / 60,
        "num_speakers": NUM_SPEAKERS,
        "processed_at": datetime.now().isoformat()
    },
    "performance": {
        "transcription_s": transcription_time,
        "diarization_s": diarization_time,
        "total_s": transcription_time + diarization_time,
        "realtime_factor": audio_duration / (transcription_time + diarization_time)
    },
    "aligned_segments": aligned_segments
}

with open(f"{OUTPUT_DIR}/transcription.json", "w") as f:
    json.dump(result, f, indent=2)

with open(f"{OUTPUT_DIR}/transcript.txt", "w") as f:
    current_speaker = None
    for seg in aligned_segments:
        if seg["speaker"] != current_speaker:
            current_speaker = seg["speaker"]
            f.write(f"\n[{current_speaker}]\n")
        f.write(f"[{seg['start']:.1f}s] {seg['text']}\n")

print(f"\nPerformance Summary:")
print(f"  Audio: {audio_duration/60:.1f} minutes")
print(f"  Total: {result['performance']['total_s']:.1f}s")
print(f"  Speed: {result['performance']['realtime_factor']:.1f}x realtime")

files.download(f"{OUTPUT_DIR}/transcription.json")
files.download(f"{OUTPUT_DIR}/transcript.txt")
```

---

## Error Log

### Error 1: `libcudnn_cnn.so.9` Not Found (RESOLVED)

**Error Message**:
```
Unable to load any of {libcudnn_cnn.so.9.1.0, libcudnn_cnn.so.9.1, libcudnn_cnn.so.9, libcudnn_cnn.so}
Invalid handle. Cannot load symbol cudnnCreateConvolutionDescriptor
kernel restarted
```

**Root Cause**:
- ctranslate2 >= 4.5.0 requires cuDNN 9.x
- Colab's PyTorch 2.5.0+cu121 uses cuDNN 8.x
- Kernel crashes when faster-whisper tries to use CUDA operations

**Failed Attempts**:
1. `torch==2.8.0` - Still crashed, torch 2.8.0 also expects cuDNN 9.x for some ops
2. `torch==2.4.0` - pyannote.audio reinstalled torch 2.8.0 as dependency
3. Installing pyannote first, then downgrading torch - Version conflicts

**Solution**:
```bash
!pip install ctranslate2==4.4.0 -q
```
Pin ctranslate2 to 4.4.0 which is the last version compatible with cuDNN 8.x.

**Status**: RESOLVED

---

### Error 2: `torchvision::nms` Operator Missing (RESOLVED)

**Error Message**:
```
RuntimeError: operator torchvision::nms does not exist
```

**Root Cause**:
- torch/torchvision version mismatch
- Colab pre-installs torchvision 0.24 (expects torch 2.9)
- torchvision registers CUDA operators at import time; mismatch = failure

**Solution**:
Don't reinstall torch/torchvision. Use Colab's default versions and only pin ctranslate2.

**Status**: RESOLVED (by not changing torch)

---

### Error 3: `use_auth_token` Deprecated (RESOLVED)

**Error Message**:
```
TypeError: Pipeline.from_pretrained() got an unexpected keyword argument 'use_auth_token'
```

**Root Cause**:
pyannote.audio 3.x+ uses `token=` parameter, not `use_auth_token=`

**Solution**:
```python
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN  # Changed from use_auth_token
)
```

**Status**: RESOLVED

---

### Error 4: `torchaudio.AudioMetaData` Not Found (CURRENT BLOCKER)

**Error Message**:
```
AttributeError: module 'torchaudio' has no attribute 'AudioMetaData'

File: /usr/local/lib/python3.12/dist-packages/pyannote/audio/core/io.py line 60
def get_torchaudio_info(file: AudioFile, backend: str = None) -> torchaudio.AudioMetaData:
```

**Root Cause**:
- `torchaudio.AudioMetaData` was renamed/moved in torchaudio 2.1+
- pyannote.audio >= 3.3.x references the old attribute name
- Colab has torchaudio 2.5.0 which doesn't have `AudioMetaData` as a direct attribute

**Attempted Solutions**:
1. `pyannote.audio>=3.1,<4.0` - Still got 3.3.x which has the issue
2. `pyannote.audio==3.1.1` - TESTING (may resolve)

**Potential Fixes to Try**:
1. Pin exact pyannote version: `pyannote.audio==3.1.1` or `==3.0.1`
2. Pin torchaudio to older version: `torchaudio==2.0.2`
3. Use WhisperX instead (bundles compatible versions)
4. Monkey-patch torchaudio at runtime

**Status**: UNRESOLVED - Testing pyannote.audio==3.1.1

---

### Error 5: Variables Lost After Session Restart (RESOLVED)

**Error Message**:
```
NameError: name 'AUDIO_FILE' is not defined
NameError: name 'whisper_model' is not defined
NameError: name 'time' is not defined
```

**Root Cause**:
- Session restart clears ALL Python variables and imports
- Cells 2+ referenced variables from Cell 2 config
- Imports done in one cell don't persist after restart

**Solution**:
- Keep all config variables in Cell 2 (runs after restart)
- Each cell should import what it needs OR
- Structure cells to be self-contained post-restart

**Status**: RESOLVED

---

### Error 6: pip Dependency Warnings (SAFE TO IGNORE)

**Error Message**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages...
google-colab 1.0.0 requires pandas==2.2.2, but you have pandas 2.3.3
opencv-python 4.12.0.88 requires numpy<2.3.0, but you have numpy 2.3.5
tensorflow 2.19.0 requires numpy<2.2.0, but you have numpy 2.3.5
```

**Root Cause**:
- Colab's environment has many pre-installed packages with strict version pins
- Our packages update numpy/pandas as dependencies
- These warnings are for packages we're NOT using

**Relevant Conflicts** (NOT safe to ignore):
```
torchvision 0.19.0+cu121 requires torch==2.4.0, but you have torch 2.8.0
```
This indicates torch version was changed - will cause crashes.

**Solution**:
- Ignore warnings about: tensorflow, opencv, google-colab, google-adk, opentelemetry
- Pay attention to: torch, torchvision, torchaudio, ctranslate2

**Status**: RESOLVED (understanding which to ignore)

---

### Error 7: Hash Mismatch During pip Install (RESOLVED)

**Error Message**:
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
```

**Root Cause**:
Corrupted or partial pip cache from previous failed installs

**Solution**:
Factory reset: Runtime → Disconnect and delete runtime

**Status**: RESOLVED

---

## Dependency Compatibility Matrix

### ctranslate2 vs cuDNN

| ctranslate2 | cuDNN Required | CUDA Required | Colab Compatible? |
|-------------|----------------|---------------|-------------------|
| <= 4.4.0 | 8.x | 11.x / 12.1 | YES |
| >= 4.5.0 | 9.x | >= 12.3 | NO (Dec 2025) |

### pyannote.audio vs torchaudio

| pyannote.audio | torchaudio | AudioMetaData Issue? |
|----------------|------------|----------------------|
| 3.0.x | 2.0.x | No |
| 3.1.x | 2.0.x - 2.1.x | No (needs testing) |
| 3.2.x | 2.1.x+ | Possibly |
| >= 3.3.x | 2.5.x | YES - current blocker |

### PyTorch Version Chain

| torch | torchvision | torchaudio | cuDNN |
|-------|-------------|------------|-------|
| 2.4.0 | 0.19.0 | 2.4.0 | 8.x |
| 2.5.0 | 0.20.0 | 2.5.0 | 8.x |
| 2.8.0 | 0.23.0 | 2.8.0 | 9.x |

---

## Key Learnings

### 1. Don't Fight Colab's PyTorch
Colab's pre-installed PyTorch (2.5.0+cu121) is carefully matched to its CUDA/cuDNN. Replacing it causes cascading failures.

### 2. Pin ctranslate2, Not PyTorch
The root cause of most crashes is ctranslate2 version, not PyTorch. Pin `ctranslate2==4.4.0`.

### 3. Install Order Matters
```bash
# CORRECT ORDER:
!pip install ctranslate2==4.4.0  # Pin first
!pip install faster-whisper       # Uses pinned version
!pip install pyannote.audio==X.X.X  # Pin to compatible version
```

### 4. Factory Reset vs Session Restart
- **Restart Session**: Clears variables, keeps installed packages
- **Disconnect and Delete Runtime**: Full factory reset, clears everything

### 5. Parameter Name Changes
- Old: `use_auth_token=`
- New: `token=`

### 6. Colab Environment is Volatile
Google updates Colab's base environment frequently. Solutions that work today may break tomorrow.

---

## Next Steps

### Immediate (Testing)

1. **Test pyannote.audio==3.1.1**
   ```bash
   !pip install pyannote.audio==3.1.1 -q
   ```
   This version may predate the torchaudio.AudioMetaData reference.

2. **If 3.1.1 fails, try 3.0.1**
   ```bash
   !pip install pyannote.audio==3.0.1 -q
   ```

3. **Alternative: Pin torchaudio**
   ```bash
   !pip install torchaudio==2.0.2 -q
   !pip install pyannote.audio -q
   ```

### Fallback Options

1. **Use WhisperX** (bundles compatible versions)
   ```bash
   !pip install git+https://github.com/m-bain/whisperx.git
   ```

2. **Monkey-patch torchaudio** (hacky but may work)
   ```python
   import torchaudio
   torchaudio.AudioMetaData = type(torchaudio.info("test.wav"))
   ```

3. **Run faster-whisper only** (skip diarization for now)
   - Get transcription working first
   - Add diarization later when dependency resolved

4. **Use different GPU provider**
   - Lambda Labs, RunPod, Vast.ai have different base environments
   - May have cuDNN 9.x available

---

## References

### GitHub Issues
- [WhisperX #902 - libcudnn_cnn.so.9 error](https://github.com/m-bain/whisperX/issues/902)
- [CTranslate2 #1806 - torch+cu121 compatibility](https://github.com/OpenNMT/CTranslate2/issues/1806)
- [faster-whisper #1086 - CUDA compatibility](https://github.com/SYSTRAN/faster-whisper/issues/1086)
- [Colab #5061 - CUDA 12.5 upgrade](https://github.com/googlecolab/colabtools/issues/5061)

### Documentation
- [pyannote.audio PyPI](https://pypi.org/project/pyannote.audio/)
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [PyTorch cuDNN Compatibility](https://www.codegenes.net/blog/pytorch-cudnn-compatibility/)

### HuggingFace Models (Accept Terms)
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

---

## Changelog

| Date | Change | Result |
|------|--------|--------|
| 2025-12-10 | Initial setup with torch 2.8.0 | libcudnn_cnn.so.9 crash |
| 2025-12-10 | Tried torch 2.4.0 | pyannote reinstalled 2.8.0 |
| 2025-12-10 | Pinned ctranslate2==4.4.0 | Resolved cuDNN crash |
| 2025-12-10 | Fixed use_auth_token → token | Resolved |
| 2025-12-10 | Hit torchaudio.AudioMetaData error | CURRENT BLOCKER |
| 2025-12-10 | Testing pyannote.audio==3.1.1 | Pending |
