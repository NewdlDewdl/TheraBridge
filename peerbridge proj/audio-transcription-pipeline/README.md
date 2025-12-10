# Audio Transcription Pipeline

Therapy session transcription with speaker diarization.

## Setup

```bash
cd audio-transcription-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python tests/test_full_pipeline.py tests/samples/onemintestvid.mp3
```

## Structure

```
src/pipeline.py          # Main pipeline classes
tests/test_full_pipeline.py  # Full pipeline with diarization
tests/samples/           # Test audio files
tests/outputs/           # Output JSON files
```

## Current Status

- Audio preprocessing
- Whisper transcription (with chunking for >25MB)
- Speaker diarization (pyannote 4.0)
- Basic alignment (in test file)
