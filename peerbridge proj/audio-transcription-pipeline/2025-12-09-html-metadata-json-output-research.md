---
date: 2025-12-09T22:20:57-06:00
researcher: newdldewdl
repository: audio-transcription-pipeline
topic: "HTML metadata values and JSON/HTML output generation"
tags: [research, codebase, transcription, html-generation, json-output, metadata, timestamps]
status: complete
last_updated: 2025-12-09
last_updated_by: newdldewdl
---

# Research: HTML Metadata Values and JSON/HTML Output Generation

**Date**: 2025-12-09T22:20:57-06:00
**Researcher**: newdldewdl
**Repository**: audio-transcription-pipeline

## Research Question
1. Why are HTML outputs showing "Unknown" for Duration and 0 for Segments/Speaker Turns?
2. How can the pipeline be extended to create JSON and HTML outputs with fewer timestamps (only when speaker changes)?

## Summary

The issue with missing metadata values in `transcription_professional.html` occurs because the formatting script reads from a JSON file (`diarization_output_improved.json`) that hasn't been generated yet. The metadata values (Duration, Language, Segments, Speaker Turns) are extracted from the Whisper API and pyannote diarization results during the full pipeline execution. The current HTML generation happens in test files separate from the main pipeline, and timestamps are generated automatically by the AI models at variable intervals based on speech patterns, not at fixed intervals.

## Detailed Findings

### HTML Generation and Missing Metadata Issue

#### Current State
- **File with issue**: `tests/outputs/transcription_professional.html` shows:
  - Duration: "Unknown"
  - Language: "english"
  - Segments: 0
  - Speaker Turns: 0

- **Working file**: `tests/outputs/diarization_output_formatted.html` shows:
  - Duration: 23:07
  - Language: English
  - Segments: 451
  - Speaker Turns: 251

#### Root Cause
The issue occurs in `tests/test_formatted_output_professional.py:409-432`:
1. Script tries to read `diarization_output_improved.json` (line 409)
2. If not found, falls back to `diarization_output.json` (line 413)
3. If neither exists, uses empty default data structure
4. Metadata extraction at lines 34-37 gets default values when JSON is missing

**Solution**: Run `test_full_pipeline_improved.py` first to generate the JSON with proper metadata, then run the formatting script.

### Metadata Extraction Flow

#### Data Sources
1. **Duration** (`test_full_pipeline.py:144-145`)
   - Source: OpenAI Whisper API `response.duration`
   - Type: Float (seconds), e.g., 1387.48
   - Requires `response_format="verbose_json"`

2. **Language** (`test_full_pipeline.py:144`)
   - Source: OpenAI Whisper API `response.language`
   - Type: String, e.g., "english"
   - Auto-detected by Whisper

3. **Segments Count** (`test_full_pipeline.py:537`)
   - Source: `len(aligned_segments)` after speaker alignment
   - Type: Integer, e.g., 451
   - Represents Whisper-detected speech segments

4. **Speaker Turns** (`test_full_pipeline.py:538`)
   - Source: `len(speaker_turns)` from pyannote diarization
   - Type: Integer, e.g., 251
   - Represents detected speaker changes

### Current JSON Output Structure

Standard output format (`test_full_pipeline.py:532-543`):
```json
{
  "metadata": {
    "source_file": "path/to/audio.mp3",
    "duration": 1387.47998046875,
    "language": "english",
    "processing_time_seconds": 283.34,
    "num_segments": 451,
    "num_speaker_turns": 251
  },
  "speaker_turns": [
    {"speaker": "SPEAKER_01", "start": 4.42, "end": 36.06}
  ],
  "diarized_segments": [
    {"start": 0.0, "end": 8.78, "text": "...", "speaker": "SPEAKER_01"}
  ],
  "full_text": "Complete transcription text..."
}
```

### Timestamp Generation Patterns

#### Current Implementation
1. **Whisper Segments** (`src/pipeline.py:180-186`)
   - Variable intervals based on speech patterns
   - Typically 1-20 seconds per segment
   - No parameter to control frequency

2. **Speaker Turns** (`test_full_pipeline.py:243-248`)
   - Based on voice characteristic changes
   - Variable duration from seconds to minutes
   - Detected by pyannote AI model

3. **Display Formats**:
   - Every segment gets timestamp: `[MM:SS]`
   - Minute markers in therapy format: `--- [M:00] ---`
   - Speaker block format shows timestamp at start

### Creating Reduced-Timestamp Output

To create JSON/HTML with timestamps only on speaker changes, a new processing step is needed:

#### Proposed Approach
1. Group consecutive segments by speaker
2. Combine text within each speaker block
3. Use speaker turn start/end times for timestamps
4. Generate simplified JSON structure
5. Create HTML with speaker-based timestamps only

#### Example Implementation Location
Add new function in `tests/test_formatted_output_professional.py`:
```python
def create_speaker_only_output(data: Dict) -> Dict:
    """Create output with timestamps only at speaker changes"""
    # Group segments by consecutive speaker
    # Combine text, keep first timestamp
    # Return simplified structure
```

## Code References

### HTML Generation
- `tests/test_formatted_output_professional.py:26` - Main HTML generation function
- `tests/test_formatted_output_professional.py:252-269` - Metadata display in HTML
- `tests/test_formatted_output.py:91` - Alternative HTML generator

### Metadata Extraction
- `test_full_pipeline.py:144-145` - Duration from Whisper
- `test_full_pipeline.py:537-538` - Segment and turn counts
- `test_full_pipeline_improved.py:439-442` - Enhanced metadata

### JSON Output
- `test_full_pipeline.py:532-543` - Standard JSON structure
- `test_full_pipeline_improved.py:435-459` - Improved JSON with metrics
- `src/pipeline_enhanced.py:644-645` - Enhanced pipeline output

### Timestamp Processing
- `src/pipeline.py:174` - Whisper timestamp configuration
- `test_full_pipeline.py:283-310` - Segment-speaker alignment
- `test_formatted_output.py:14-18` - Time formatting function

## Architecture Documentation

### Pipeline Flow
1. Audio preprocessing → Single MP3 file
2. Whisper transcription → Segments with timestamps
3. Speaker diarization → Speaker turns with timestamps
4. Alignment → Segments assigned to speakers
5. JSON generation → Complete data structure
6. HTML formatting → Reads JSON and generates display

### File Dependencies
- Pipeline creates: `diarization_output.json` or `diarization_output_improved.json`
- Formatters read: JSON files from `tests/outputs/`
- Formatters create: HTML/Markdown in same directory

### Key Design Patterns
- Metadata stored in top-level dictionary
- Timestamps as float seconds in data, MM:SS in display
- Speaker labels: "SPEAKER_00", "SPEAKER_01", "UNKNOWN"
- JSON with `indent=2` for readability

## Open Questions

1. Should the HTML generation be integrated into the main pipeline rather than separate test files?
2. What should be the logic for determining "significant" speaker changes for reduced timestamps?
3. Should the reduced-timestamp version be a separate output file or a configuration option?
4. How should overlapping speech be handled in the simplified output?

## Recommendations for Implementation

### Fix Missing Metadata Values
1. Ensure pipeline runs before formatting: `python test_full_pipeline_improved.py` then `python test_formatted_output_professional.py`
2. Or integrate HTML generation into pipeline to ensure data availability

### Add Reduced-Timestamp Output
1. Create new processing function to group segments by speaker
2. Add configuration option for timestamp frequency
3. Generate both detailed and simplified outputs
4. Consider speaker labeling (Therapist/Client) for clarity