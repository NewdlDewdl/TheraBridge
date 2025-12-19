#!/usr/bin/env python3
"""
CPU Pipeline Test for File 2: LIVE Cognitive Behavioral Therapy Session (1).mp3
Instance I3 - CPU/API pipeline testing specialist
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Optional psutil for memory tracking
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Load environment variables
load_dotenv()

# Import pipeline components from test_full_pipeline.py
import sys
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_full_pipeline import (
    AudioPreprocessor,
    WhisperTranscriber,
    SpeakerDiarizer,
    align_speakers_with_segments,
    transcribe_with_chunks
)

def get_memory_usage_mb():
    """Get current process memory usage in MB"""
    if PSUTIL_AVAILABLE:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    return 0.0

def calculate_alignment_quality(segments):
    """Calculate percentage of segments with UNKNOWN speaker"""
    if not segments:
        return 0.0
    unknown_count = sum(1 for seg in segments if seg.get("speaker") == "UNKNOWN")
    return (unknown_count / len(segments)) * 100

def main():
    print("=" * 80)
    print("CPU/API PIPELINE TEST - FILE 2")
    print("Instance I3 - CPU/API Pipeline Testing Specialist")
    print("=" * 80)

    # File details
    audio_file = Path("/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/tests/samples/LIVE Cognitive Behavioral Therapy Session (1).mp3")

    if not audio_file.exists():
        print(f"ERROR: Audio file not found: {audio_file}")
        return

    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"\nAudio file: {audio_file.name}")
    print(f"File size: {file_size_mb:.2f}MB")

    # Performance tracking
    performance = {
        "preprocessing_time": 0,
        "whisper_api_time": 0,
        "diarization_time": 0,
        "alignment_time": 0,
        "total_time": 0,
        "memory_peak_mb": 0,
        "memory_start_mb": get_memory_usage_mb()
    }

    total_start = time.time()

    # ============================================================================
    # STAGE 1: PREPROCESSING
    # ============================================================================
    print("\n" + "=" * 80)
    print("STAGE 1: AUDIO PREPROCESSING")
    print("=" * 80)
    print("Converting 44.1kHz stereo → 16kHz mono...")

    preprocess_start = time.time()
    preprocessor = AudioPreprocessor(output_format="mp3")

    output_dir = Path(__file__).parent / "tests" / "processed"
    output_dir.mkdir(exist_ok=True)

    processed_audio = preprocessor.preprocess(
        str(audio_file),
        str(output_dir / "file2_processed.mp3")
    )

    performance["preprocessing_time"] = time.time() - preprocess_start
    performance["memory_peak_mb"] = max(performance["memory_peak_mb"], get_memory_usage_mb())

    print(f"✓ Preprocessing complete in {performance['preprocessing_time']:.2f}s")
    print(f"  Processed file: {processed_audio}")
    if PSUTIL_AVAILABLE:
        print(f"  Memory usage: {get_memory_usage_mb():.1f}MB")

    # ============================================================================
    # STAGE 2: WHISPER API TRANSCRIPTION
    # ============================================================================
    print("\n" + "=" * 80)
    print("STAGE 2: WHISPER API TRANSCRIPTION")
    print("=" * 80)
    print("Uploading to OpenAI Whisper API...")

    whisper_start = time.time()
    transcriber = WhisperTranscriber()
    transcription = transcribe_with_chunks(transcriber, processed_audio)

    performance["whisper_api_time"] = time.time() - whisper_start
    performance["memory_peak_mb"] = max(performance["memory_peak_mb"], get_memory_usage_mb())

    print(f"✓ Transcription complete in {performance['whisper_api_time']:.2f}s")
    print(f"  Duration: {transcription['duration']:.1f}s ({transcription['duration']/60:.1f} minutes)")
    print(f"  Language: {transcription['language']}")
    print(f"  Segments: {len(transcription['segments'])}")
    if PSUTIL_AVAILABLE:
        print(f"  Memory usage: {get_memory_usage_mb():.1f}MB")

    # ============================================================================
    # STAGE 3: SPEAKER DIARIZATION
    # ============================================================================
    print("\n" + "=" * 80)
    print("STAGE 3: SPEAKER DIARIZATION (Pyannote)")
    print("=" * 80)
    print("Loading model and analyzing speakers...")

    diarize_start = time.time()
    diarizer = SpeakerDiarizer(num_speakers=2)
    speaker_turns = diarizer.diarize(processed_audio)

    performance["diarization_time"] = time.time() - diarize_start
    performance["memory_peak_mb"] = max(performance["memory_peak_mb"], get_memory_usage_mb())

    print(f"✓ Diarization complete in {performance['diarization_time']:.2f}s")
    print(f"  Speaker turns: {len(speaker_turns)}")
    if PSUTIL_AVAILABLE:
        print(f"  Memory usage: {get_memory_usage_mb():.1f}MB")

    # Count turns per speaker
    speaker_counts = {}
    for turn in speaker_turns:
        speaker = turn["speaker"]
        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
    print(f"  Speaker distribution: {speaker_counts}")

    # ============================================================================
    # STAGE 4: ALIGNMENT
    # ============================================================================
    print("\n" + "=" * 80)
    print("STAGE 4: ALIGNMENT")
    print("=" * 80)
    print("Matching speakers to text segments...")

    align_start = time.time()
    aligned_segments = align_speakers_with_segments(transcription['segments'], speaker_turns)

    performance["alignment_time"] = time.time() - align_start
    performance["total_time"] = time.time() - total_start

    print(f"✓ Alignment complete in {performance['alignment_time']:.2f}s")

    # ============================================================================
    # QUALITY METRICS
    # ============================================================================
    alignment_quality = calculate_alignment_quality(aligned_segments)
    speed_ratio = transcription['duration'] / performance['total_time']

    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    print(f"Preprocessing time:    {performance['preprocessing_time']:>8.2f}s")
    print(f"Whisper API time:      {performance['whisper_api_time']:>8.2f}s")
    print(f"Diarization time:      {performance['diarization_time']:>8.2f}s")
    print(f"Alignment time:        {performance['alignment_time']:>8.2f}s")
    print(f"Total processing time: {performance['total_time']:>8.2f}s")
    print(f"Audio duration:        {transcription['duration']:>8.2f}s ({transcription['duration']/60:.1f} min)")
    print(f"Speed ratio:           {speed_ratio:>8.2f}x real-time")
    if PSUTIL_AVAILABLE:
        print(f"Peak memory usage:     {performance['memory_peak_mb']:>8.1f}MB")

    print("\n" + "=" * 80)
    print("QUALITY METRICS")
    print("=" * 80)
    print(f"Total segments:        {len(aligned_segments)}")
    print(f"Total speaker turns:   {len(speaker_turns)}")
    print(f"Speaker alignment:     {100 - alignment_quality:.1f}% identified")
    print(f"Unknown segments:      {alignment_quality:.1f}%")

    # Status determination
    status = "PASS" if alignment_quality < 30 else "PASS (with warnings)"
    if alignment_quality >= 50:
        status = "FAIL (poor alignment quality)"

    print(f"\nStatus: {status}")

    # ============================================================================
    # SAVE RESULTS
    # ============================================================================
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)

    # Save full transcription output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "tests" / "outputs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"cpu_pipeline_file2_{timestamp}.json"

    output = {
        "metadata": {
            "test_id": "cpu_pipeline_file2",
            "instance": "I3",
            "role": "CPU/API pipeline testing specialist",
            "source_file": str(audio_file),
            "file_size_mb": file_size_mb,
            "duration_seconds": transcription['duration'],
            "language": transcription['language'],
            "timestamp": timestamp,
            "pipeline_type": "CPU/API",
            "device": "CPU with OpenAI Whisper API"
        },
        "performance": {
            "preprocessing_time_seconds": performance['preprocessing_time'],
            "whisper_api_time_seconds": performance['whisper_api_time'],
            "diarization_time_seconds": performance['diarization_time'],
            "alignment_time_seconds": performance['alignment_time'],
            "total_time_seconds": performance['total_time'],
            "speed_ratio": speed_ratio,
            "peak_memory_mb": performance['memory_peak_mb']
        },
        "quality": {
            "total_segments": len(aligned_segments),
            "total_speaker_turns": len(speaker_turns),
            "speaker_distribution": speaker_counts,
            "alignment_quality_percent": 100 - alignment_quality,
            "unknown_segments_percent": alignment_quality
        },
        "segments": transcription['segments'],
        "speaker_turns": speaker_turns,
        "diarized_segments": aligned_segments,
        "full_text": transcription['full_text'],
        "status": status
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✓ Full output saved to: {output_file}")

    # Save performance summary
    summary_file = output_dir / f"cpu_pipeline_file2_summary_{timestamp}.json"
    summary = {
        "test_id": "cpu_pipeline_file2",
        "timestamp": timestamp,
        "file": audio_file.name,
        "preprocessing_time_seconds": performance['preprocessing_time'],
        "whisper_api_time_seconds": performance['whisper_api_time'],
        "diarization_time_seconds": performance['diarization_time'],
        "total_time_seconds": performance['total_time'],
        "audio_duration_seconds": transcription['duration'],
        "speed_ratio": speed_ratio,
        "peak_memory_mb": performance['memory_peak_mb'],
        "total_segments": len(aligned_segments),
        "total_speaker_turns": len(speaker_turns),
        "alignment_quality_percent": 100 - alignment_quality,
        "unknown_segments_percent": alignment_quality,
        "status": status
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Performance summary saved to: {summary_file}")

    # Cleanup temp file
    temp_file = Path(processed_audio)
    if temp_file.exists():
        temp_file.unlink()
        print("✓ Cleaned up temp file")

    # ============================================================================
    # FINAL REPORT
    # ============================================================================
    print("\n" + "=" * 80)
    print("DELIVERABLES SUMMARY")
    print("=" * 80)
    print(f"""
Instance: I3 (CPU/API Pipeline Testing Specialist)
File: {audio_file.name}
Size: {file_size_mb:.1f}MB
Duration: {transcription['duration']/60:.1f} minutes

PERFORMANCE:
- Preprocessing: {performance['preprocessing_time']:.1f}s (44.1kHz→16kHz conversion)
- Whisper API: {performance['whisper_api_time']:.1f}s
- Diarization: {performance['diarization_time']:.1f}s
- Total: {performance['total_time']:.1f}s ({speed_ratio:.2f}x real-time)
- Peak memory: {performance['memory_peak_mb']:.1f}MB

QUALITY:
- Segments: {len(aligned_segments)}
- Speaker turns: {len(speaker_turns)}
- Speakers: {len(speaker_counts)}
- Alignment: {100 - alignment_quality:.1f}% identified ({alignment_quality:.1f}% unknown)

OUTPUT:
- Full JSON: {output_file.name}
- Summary: {summary_file.name}
- Status: {status}
    """.strip())

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
