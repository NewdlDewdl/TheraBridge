# Google Colab GPU Audio Pipeline - Implementation Plan

## Overview

Connect Google Colab L4 GPU to the audio transcription pipeline to achieve 10-15x realtime processing for the compressed m4a test file. This plan resolves the **`torchaudio.AudioMetaData` error** that is currently blocking pyannote.audio diarization.

## Current State Analysis

### The Problem
- **Error**: `AttributeError: module 'torchaudio' has no attribute 'AudioMetaData'`
- **Root Cause**: torchaudio 2.9+ (November 2025) removed `AudioMetaData` class
- **Impact**: pyannote.audio 3.x depends on this class and fails on Colab's default environment

### Key Discoveries
1. Colab's default PyTorch 2.5.0+cu121 uses cuDNN 8.x (not 9.x)
2. ctranslate2 >= 4.5.0 requires cuDNN 9.x → must pin to 4.4.0
3. pyannote.audio 4.0+ uses `torchcodec` instead of `torchaudio` → **solves AudioMetaData issue**
4. Alternative: Pin torch/torchaudio to 2.3.1 with pyannote.audio 3.3.2

## Desired End State

- Successfully transcribe `compressed-cbt-session.m4a` with speaker diarization
- Achieve 10-15x realtime processing speed on L4 GPU
- Output JSON with aligned speaker segments and transcript

## What We're NOT Doing

- Not changing local pipeline code
- Not using alternative GPU providers (staying on Colab)
- Not skipping diarization (full pipeline required)

---

## Implementation Approach

**Strategy**: Use pyannote.audio 4.0.3 (latest) which uses `torchcodec` instead of `torchaudio`, completely avoiding the AudioMetaData issue.

**Fallback**: If 4.0.3 fails, use version-locked pyannote.audio 3.3.2 with torch 2.3.1.

---

## Phase 1: Colab Cell Implementation (Primary Solution - pyannote 4.0.3)

### Prerequisites

1. **Factory Reset Colab**: Runtime → Disconnect and delete runtime
2. **Set L4 GPU**: Runtime → Change runtime type → L4
3. **Accept HuggingFace Terms** (REQUIRED - do this in browser first):
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

---

### Cell 1: System Dependencies & Core Installation

```python
# ============================================================
# CELL 1: System Dependencies & Core Installation
# ============================================================
# Run this cell FIRST after factory reset

# Install system dependencies
!apt-get update -qq
!apt-get install -y -qq ffmpeg

# Pin ctranslate2 for cuDNN 8.x compatibility (CRITICAL)
!pip install ctranslate2==4.4.0 -q

# Install faster-whisper (uses pinned ctranslate2)
!pip install faster-whisper -q

# Install pyannote.audio 4.0.3 (uses torchcodec, NOT torchaudio)
# This SOLVES the AudioMetaData error
!pip install pyannote.audio==4.0.3 -q

# Verify installations
import torch
import ctranslate2
print(f"✓ torch: {torch.__version__}")
print(f"✓ ctranslate2: {ctranslate2.__version__}")
print(f"✓ CUDA: {torch.version.cuda}")
print(f"✓ cuDNN: {torch.backends.cudnn.version()}")
print(f"✓ GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NOT AVAILABLE'}")
```

**Expected Output**:
```
✓ torch: 2.5.0+cu121
✓ ctranslate2: 4.4.0
✓ CUDA: 12.1
✓ cuDNN: 8700
✓ GPU: NVIDIA L4
```

---

### Cell 2: Configuration & Audio Upload

```python
# ============================================================
# CELL 2: Configuration & Audio Upload
# ============================================================
import torch
import os
import time
from google.colab import files

# Configuration
HF_TOKEN = "YOUR_HF_TOKEN_HERE"
AUDIO_FILE = "/content/compressed-cbt-session.m4a"
NUM_SPEAKERS = 2
LANGUAGE = "en"
WHISPER_MODEL = "large-v3"
OUTPUT_DIR = "/content/output"

# Verify GPU
if not torch.cuda.is_available():
    raise RuntimeError("❌ CUDA not available! Set runtime to L4 GPU")

print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
print(f"✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Upload audio file
if not os.path.exists(AUDIO_FILE):
    print("\n📁 Upload compressed-cbt-session.m4a:")
    uploaded = files.upload()
    if uploaded:
        uploaded_name = list(uploaded.keys())[0]
        AUDIO_FILE = f"/content/{uploaded_name}"
        print(f"✓ Uploaded: {AUDIO_FILE}")
else:
    print(f"✓ Audio file exists: {AUDIO_FILE}")

# Show file info
if os.path.exists(AUDIO_FILE):
    file_size_mb = os.path.getsize(AUDIO_FILE) / (1024 * 1024)
    print(f"✓ File size: {file_size_mb:.2f} MB")
```

---

### Cell 3: Load Whisper Model

```python
# ============================================================
# CELL 3: Load Whisper Model (faster-whisper with GPU)
# ============================================================
from faster_whisper import WhisperModel

print(f"🔄 Loading Whisper {WHISPER_MODEL}...")
load_start = time.time()

whisper_model = WhisperModel(
    WHISPER_MODEL,
    device="cuda",
    compute_type="float16"  # Use FP16 for L4 GPU
)

print(f"✓ Whisper loaded in {time.time() - load_start:.1f}s")
print(f"✓ Model: {WHISPER_MODEL}")
print(f"✓ Device: cuda (float16)")
```

---

### Cell 4: Load Pyannote Diarization Pipeline

```python
# ============================================================
# CELL 4: Load Pyannote Diarization Pipeline
# ============================================================
from pyannote.audio import Pipeline

print("🔄 Loading Pyannote speaker-diarization-3.1...")
load_start = time.time()

# pyannote.audio 4.0+ uses 'token' parameter (not 'use_auth_token')
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)

# Move to GPU
diarization_pipeline.to(torch.device("cuda"))

print(f"✓ Pyannote loaded in {time.time() - load_start:.1f}s")
print(f"✓ Pipeline on GPU: cuda")
```

**If you get an authentication error**:
1. Go to https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree and access repository"
3. Do the same for https://huggingface.co/pyannote/segmentation-3.0
4. Re-run this cell

---

### Cell 5: Transcribe Audio with Whisper

```python
# ============================================================
# CELL 5: Transcribe Audio with Whisper
# ============================================================
print(f"🎤 Transcribing: {AUDIO_FILE}")
transcribe_start = time.time()

segments_raw, info = whisper_model.transcribe(
    AUDIO_FILE,
    language=LANGUAGE,
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500)
)

# Convert generator to list
transcription_segments = [
    {"start": s.start, "end": s.end, "text": s.text.strip()}
    for s in segments_raw
]

audio_duration = info.duration
transcription_time = time.time() - transcribe_start

print(f"✓ Segments: {len(transcription_segments)}")
print(f"✓ Duration: {audio_duration/60:.1f} minutes")
print(f"✓ Time: {transcription_time:.1f}s")
print(f"✓ Speed: {audio_duration/transcription_time:.1f}x realtime")
```

---

### Cell 6: Run Speaker Diarization

```python
# ============================================================
# CELL 6: Run Speaker Diarization
# ============================================================
import torchaudio

print(f"🎭 Running speaker diarization...")
diarize_start = time.time()

# Load audio for diarization
waveform, sample_rate = torchaudio.load(AUDIO_FILE)

# Run diarization with in-memory audio (faster)
diarization_result = diarization_pipeline(
    {"waveform": waveform, "sample_rate": sample_rate},
    num_speakers=NUM_SPEAKERS
)

# Extract speaker turns
speaker_turns = [
    {"speaker": spk, "start": turn.start, "end": turn.end}
    for turn, _, spk in diarization_result.itertracks(yield_label=True)
]

diarization_time = time.time() - diarize_start

print(f"✓ Speaker turns: {len(speaker_turns)}")
print(f"✓ Time: {diarization_time:.1f}s")
print(f"✓ Speed: {audio_duration/diarization_time:.1f}x realtime")
```

---

### Cell 7: Align Transcription with Speakers (GPU-accelerated)

```python
# ============================================================
# CELL 7: Align Transcription with Speakers (GPU-accelerated)
# ============================================================
print("🔗 Aligning transcription segments with speakers...")

# Convert to GPU tensors for fast alignment
seg_starts = torch.tensor([s["start"] for s in transcription_segments], device="cuda")
seg_ends = torch.tensor([s["end"] for s in transcription_segments], device="cuda")
turn_starts = torch.tensor([t["start"] for t in speaker_turns], device="cuda")
turn_ends = torch.tensor([t["end"] for t in speaker_turns], device="cuda")

# Calculate overlap matrix (GPU)
overlaps = torch.clamp(
    torch.minimum(seg_ends.unsqueeze(1), turn_ends) -
    torch.maximum(seg_starts.unsqueeze(1), turn_starts),
    min=0
)

# Find best matching speaker for each segment
max_overlaps, best_idx = torch.max(overlaps, dim=1)

# Only assign speaker if overlap > 50% of segment duration
segment_durations = seg_ends - seg_starts
threshold_mask = (max_overlaps / segment_durations) >= 0.5

# Build aligned segments
aligned_segments = []
for i, seg in enumerate(transcription_segments):
    if threshold_mask[i]:
        speaker = speaker_turns[best_idx[i].item()]["speaker"]
    else:
        speaker = "UNKNOWN"
    aligned_segments.append({**seg, "speaker": speaker})

print(f"✓ Aligned {len(aligned_segments)} segments with speakers")

# Preview first few segments
print("\n📝 Preview (first 5 segments):")
for seg in aligned_segments[:5]:
    print(f"  [{seg['speaker']}] {seg['start']:.1f}s-{seg['end']:.1f}s: {seg['text'][:50]}...")
```

---

### Cell 8: Save Results & Download

```python
# ============================================================
# CELL 8: Save Results & Download
# ============================================================
import json
from datetime import datetime

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Build result object
total_time = transcription_time + diarization_time
result = {
    "metadata": {
        "source_file": os.path.basename(AUDIO_FILE),
        "duration_minutes": audio_duration / 60,
        "num_speakers": NUM_SPEAKERS,
        "whisper_model": WHISPER_MODEL,
        "language": LANGUAGE,
        "processed_at": datetime.now().isoformat(),
        "gpu": torch.cuda.get_device_name(0)
    },
    "performance": {
        "transcription_seconds": round(transcription_time, 2),
        "diarization_seconds": round(diarization_time, 2),
        "total_seconds": round(total_time, 2),
        "realtime_factor": round(audio_duration / total_time, 1)
    },
    "segments": aligned_segments
}

# Save JSON
json_path = f"{OUTPUT_DIR}/transcription.json"
with open(json_path, "w") as f:
    json.dump(result, f, indent=2)

# Save human-readable transcript
txt_path = f"{OUTPUT_DIR}/transcript.txt"
with open(txt_path, "w") as f:
    f.write(f"# Transcript: {os.path.basename(AUDIO_FILE)}\n")
    f.write(f"# Duration: {audio_duration/60:.1f} minutes\n")
    f.write(f"# Processed: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"# Speed: {result['performance']['realtime_factor']}x realtime\n\n")

    current_speaker = None
    for seg in aligned_segments:
        if seg["speaker"] != current_speaker:
            current_speaker = seg["speaker"]
            f.write(f"\n[{current_speaker}]\n")
        f.write(f"[{seg['start']:.1f}s] {seg['text']}\n")

# Print summary
print("=" * 60)
print("📊 PERFORMANCE SUMMARY")
print("=" * 60)
print(f"  Audio Duration:    {audio_duration/60:.1f} minutes")
print(f"  Transcription:     {transcription_time:.1f}s ({audio_duration/transcription_time:.1f}x realtime)")
print(f"  Diarization:       {diarization_time:.1f}s ({audio_duration/diarization_time:.1f}x realtime)")
print(f"  Total Processing:  {total_time:.1f}s")
print(f"  Overall Speed:     {result['performance']['realtime_factor']}x realtime")
print("=" * 60)

# Download files
print("\n📥 Downloading results...")
files.download(json_path)
files.download(txt_path)
print("✓ Download complete!")
```

---

## Phase 2: Fallback Solution (If Phase 1 Fails)

If pyannote.audio 4.0.3 has issues, use this version-locked approach:

### Fallback Cell 1: Version-Locked Installation

```python
# ============================================================
# FALLBACK CELL 1: Version-Locked Installation
# ============================================================
# Use if pyannote.audio 4.0.3 fails

!apt-get update -qq
!apt-get install -y -qq ffmpeg

# Pin ALL versions explicitly
!pip install torch==2.3.1 torchaudio==2.3.1 torchvision==0.18.1 -q
!pip install ctranslate2==4.4.0 -q
!pip install faster-whisper -q
!pip install pyannote.audio==3.3.2 -q

# Verify
import torch
import torchaudio
print(f"✓ torch: {torch.__version__}")
print(f"✓ torchaudio: {torchaudio.__version__}")

# Check AudioMetaData exists
if hasattr(torchaudio, 'AudioMetaData'):
    print("✓ torchaudio.AudioMetaData: EXISTS")
else:
    print("❌ torchaudio.AudioMetaData: MISSING (will fail)")
```

**Then run Cells 2-8 from Phase 1** (they work with both versions).

---

## Phase 3: Emergency Monkey-Patch (Last Resort)

If both solutions fail, apply this monkey-patch before importing pyannote:

### Emergency Cell: Monkey-Patch AudioMetaData

```python
# ============================================================
# EMERGENCY: Monkey-Patch AudioMetaData
# ============================================================
# Use ONLY if Phase 1 and Phase 2 both fail

import torchaudio
from dataclasses import dataclass

if not hasattr(torchaudio, 'AudioMetaData'):
    @dataclass
    class AudioMetaData:
        sample_rate: int
        num_frames: int
        num_channels: int
        bits_per_sample: int = 0
        encoding: str = ""

    torchaudio.AudioMetaData = AudioMetaData
    print("✓ Monkey-patched torchaudio.AudioMetaData")
else:
    print("✓ torchaudio.AudioMetaData already exists")

# NOW safe to import pyannote
from pyannote.audio import Pipeline
print("✓ pyannote.audio imported successfully")
```

---

## Success Criteria

### Automated Verification
- [ ] Cell 1 completes without cuDNN errors
- [ ] Cell 3 loads Whisper model on GPU
- [ ] Cell 4 loads pyannote pipeline without AudioMetaData error
- [ ] Cell 5 transcription achieves >10x realtime
- [ ] Cell 6 diarization completes successfully
- [ ] Cell 8 downloads JSON and TXT files

### Manual Verification
- [ ] Transcript text is accurate
- [ ] Speaker labels (SPEAKER_00, SPEAKER_01) are correctly assigned
- [ ] No segments labeled "UNKNOWN" (or minimal)
- [ ] JSON output can be parsed by downstream pipeline

---

## Troubleshooting Guide

| Error | Cause | Solution |
|-------|-------|----------|
| `libcudnn_cnn.so.9` | ctranslate2 too new | Pin `ctranslate2==4.4.0` |
| `AudioMetaData not found` | torchaudio 2.9+ | Use pyannote 4.0.3 or pin torch 2.3.1 |
| `401 Unauthorized` | HF token invalid | Check token, accept model terms |
| `CUDA out of memory` | Model too large | Use `large-v2` instead of `large-v3` |
| `kernel restarted` | Version conflict | Factory reset and follow exact order |

---

## References

- [pyannote-audio Issue #1952 - AudioMetaData fix](https://github.com/pyannote/pyannote-audio/issues/1952)
- [pyannote.audio 4.0 CHANGELOG](https://github.com/pyannote/pyannote-audio/blob/main/CHANGELOG.md)
- [WhisperX Issue #1270 - Colab compatibility](https://github.com/m-bain/whisperX/issues/1270)
- [CTranslate2 Issue #1806 - cuDNN 8.x compatibility](https://github.com/OpenNMT/CTranslate2/issues/1806)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-10 | Initial plan created with pyannote 4.0.3 solution |
