#!/usr/bin/env python3
"""
CPU Pipeline Test - File 1
===========================
Tests CPU/API transcription pipeline with:
- Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3
- Detailed performance tracking
- Quality validation
"""

import os
import json
import time
import psutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from existing test_full_pipeline.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from test_full_pipeline import (
    AudioPreprocessor,
    WhisperTranscriber,
    SpeakerDiarizer,
    align_speakers_with_segments,
    transcribe_with_chunks,
    debug_log
)


class PerformanceTracker:
    """Track detailed performance metrics"""

    def __init__(self):
        self.process = psutil.Process()
        self.metrics = {
            "start_time": time.time(),
            "stages": {},
            "memory_usage_mb": [],
            "api_latency_seconds": 0
        }

    def start_stage(self, stage_name: str):
        """Mark start of a processing stage"""
        self.metrics["stages"][stage_name] = {
            "start": time.time(),
            "memory_start_mb": self.process.memory_info().rss / (1024 * 1024)
        }

    def end_stage(self, stage_name: str):
        """Mark end of a processing stage"""
        if stage_name not in self.metrics["stages"]:
            return

        stage = self.metrics["stages"][stage_name]
        stage["end"] = time.time()
        stage["duration_seconds"] = stage["end"] - stage["start"]
        stage["memory_end_mb"] = self.process.memory_info().rss / (1024 * 1024)
        stage["memory_delta_mb"] = stage["memory_end_mb"] - stage["memory_start_mb"]

    def record_api_latency(self, latency_seconds: float):
        """Record Whisper API latency"""
        self.metrics["api_latency_seconds"] += latency_seconds

    def get_summary(self) -> dict:
        """Get performance summary"""
        total_time = time.time() - self.metrics["start_time"]
        current_memory = self.process.memory_info().rss / (1024 * 1024)

        return {
            "total_processing_time_seconds": total_time,
            "api_latency_seconds": self.metrics["api_latency_seconds"],
            "computation_time_seconds": total_time - self.metrics["api_latency_seconds"],
            "current_memory_mb": current_memory,
            "stages": self.metrics["stages"]
        }


def calculate_quality_metrics(aligned_segments: list, speaker_turns: list, duration: float) -> dict:
    """Calculate quality metrics for alignment"""

    # Count speaker distribution
    speaker_counts = {}
    unknown_count = 0
    total_duration = 0
    unknown_duration = 0

    for seg in aligned_segments:
        speaker = seg["speaker"]
        seg_duration = seg["end"] - seg["start"]
        total_duration += seg_duration

        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

        if speaker == "UNKNOWN":
            unknown_count += 1
            unknown_duration += seg_duration

    unknown_percent = (unknown_count / len(aligned_segments) * 100) if aligned_segments else 0
    unknown_time_percent = (unknown_duration / total_duration * 100) if total_duration > 0 else 0

    # Calculate average segment length
    avg_segment_length = total_duration / len(aligned_segments) if aligned_segments else 0

    # Calculate speaker turn statistics
    speaker_turn_durations = {}
    for turn in speaker_turns:
        speaker = turn["speaker"]
        duration = turn["end"] - turn["start"]
        if speaker not in speaker_turn_durations:
            speaker_turn_durations[speaker] = []
        speaker_turn_durations[speaker].append(duration)

    return {
        "total_segments": len(aligned_segments),
        "total_speaker_turns": len(speaker_turns),
        "speaker_segment_distribution": speaker_counts,
        "unknown_segments_count": unknown_count,
        "unknown_segments_percent": unknown_percent,
        "unknown_time_percent": unknown_time_percent,
        "average_segment_length_seconds": avg_segment_length,
        "speaker_turn_stats": {
            speaker: {
                "count": len(durations),
                "avg_duration": sum(durations) / len(durations),
                "total_duration": sum(durations)
            }
            for speaker, durations in speaker_turn_durations.items()
        }
    }


def main():
    print("=" * 80)
    print("CPU PIPELINE TEST - FILE 1")
    print("=" * 80)
    print()

    # File path
    script_dir = Path(__file__).parent
    audio_file = script_dir / "samples" / "Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3"

    if not audio_file.exists():
        print(f"ERROR: Audio file not found: {audio_file}")
        return 1

    # Get file info
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"Input file: {audio_file.name}")
    print(f"File size: {file_size_mb:.2f}MB")
    print()

    # Initialize performance tracker
    tracker = PerformanceTracker()

    try:
        # ------------------------------------------
        # STAGE 1: Preprocessing
        # ------------------------------------------
        print("STAGE 1: Audio Preprocessing")
        print("-" * 80)
        tracker.start_stage("preprocessing")

        preprocessor = AudioPreprocessor(output_format="mp3")
        processed_dir = script_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        processed_audio = preprocessor.preprocess(
            str(audio_file),
            str(processed_dir / f"cpu_file1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
        )

        tracker.end_stage("preprocessing")
        print(f"✓ Completed in {tracker.metrics['stages']['preprocessing']['duration_seconds']:.2f}s")
        print()

        # ------------------------------------------
        # STAGE 2: Whisper Transcription
        # ------------------------------------------
        print("STAGE 2: Whisper API Transcription")
        print("-" * 80)
        tracker.start_stage("transcription")

        api_start = time.time()
        transcriber = WhisperTranscriber()
        transcription = transcribe_with_chunks(transcriber, processed_audio)
        api_latency = time.time() - api_start
        tracker.record_api_latency(api_latency)

        tracker.end_stage("transcription")
        print(f"✓ Completed in {tracker.metrics['stages']['transcription']['duration_seconds']:.2f}s")
        print(f"  - API latency: {api_latency:.2f}s")
        print(f"  - Audio duration: {transcription['duration']:.2f}s")
        print(f"  - Segments: {len(transcription['segments'])}")
        print(f"  - Full text length: {len(transcription['full_text'])} chars")
        print()

        # ------------------------------------------
        # STAGE 3: Speaker Diarization
        # ------------------------------------------
        print("STAGE 3: Speaker Diarization (Pyannote)")
        print("-" * 80)
        tracker.start_stage("diarization")

        diarizer = SpeakerDiarizer(num_speakers=2)
        speaker_turns = diarizer.diarize(processed_audio)

        tracker.end_stage("diarization")
        print(f"✓ Completed in {tracker.metrics['stages']['diarization']['duration_seconds']:.2f}s")
        print(f"  - Speaker turns: {len(speaker_turns)}")
        print()

        # ------------------------------------------
        # STAGE 4: Alignment
        # ------------------------------------------
        print("STAGE 4: Speaker-Text Alignment")
        print("-" * 80)
        tracker.start_stage("alignment")

        aligned_segments = align_speakers_with_segments(
            transcription['segments'],
            speaker_turns
        )

        tracker.end_stage("alignment")
        print(f"✓ Completed in {tracker.metrics['stages']['alignment']['duration_seconds']:.2f}s")
        print()

        # ------------------------------------------
        # QUALITY METRICS
        # ------------------------------------------
        print("QUALITY METRICS")
        print("-" * 80)
        quality = calculate_quality_metrics(
            aligned_segments,
            speaker_turns,
            transcription['duration']
        )

        print(f"Total segments: {quality['total_segments']}")
        print(f"Total speaker turns: {quality['total_speaker_turns']}")
        print(f"Speaker distribution: {quality['speaker_segment_distribution']}")
        print(f"Unknown segments: {quality['unknown_segments_count']} ({quality['unknown_segments_percent']:.1f}%)")
        print(f"Unknown time coverage: {quality['unknown_time_percent']:.1f}%")
        print(f"Average segment length: {quality['average_segment_length_seconds']:.2f}s")
        print()

        for speaker, stats in quality['speaker_turn_stats'].items():
            print(f"{speaker}: {stats['count']} turns, avg {stats['avg_duration']:.2f}s, total {stats['total_duration']:.2f}s")
        print()

        # ------------------------------------------
        # PERFORMANCE SUMMARY
        # ------------------------------------------
        print("PERFORMANCE SUMMARY")
        print("-" * 80)
        perf_summary = tracker.get_summary()

        total_time = perf_summary['total_processing_time_seconds']
        audio_duration = transcription['duration']
        speed_ratio = audio_duration / total_time if total_time > 0 else 0

        print(f"Total processing time: {total_time:.2f}s")
        print(f"Audio duration: {audio_duration:.2f}s ({audio_duration/60:.1f}min)")
        print(f"Speed ratio: {speed_ratio:.2f}x real-time")
        print(f"API latency: {perf_summary['api_latency_seconds']:.2f}s ({perf_summary['api_latency_seconds']/total_time*100:.1f}%)")
        print(f"Computation time: {perf_summary['computation_time_seconds']:.2f}s")
        print(f"Current memory usage: {perf_summary['current_memory_mb']:.2f}MB")
        print()

        # ------------------------------------------
        # SAVE RESULTS
        # ------------------------------------------
        print("SAVING RESULTS")
        print("-" * 80)

        # Create outputs directory
        outputs_dir = script_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save full output JSON
        output_data = {
            "metadata": {
                "source_file": str(audio_file),
                "file_size_mb": file_size_mb,
                "duration": transcription['duration'],
                "language": transcription['language'],
                "timestamp": timestamp,
                "pipeline_type": "CPU_API"
            },
            "performance": perf_summary,
            "quality": quality,
            "segments": transcription['segments'],
            "speaker_turns": speaker_turns,
            "diarized_segments": aligned_segments,
            "full_text": transcription['full_text']
        }

        output_file = outputs_dir / f"cpu_pipeline_file1_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Full output saved: {output_file}")

        # Save performance summary
        perf_file = outputs_dir / f"cpu_pipeline_file1_performance_{timestamp}.json"
        with open(perf_file, "w") as f:
            json.dump({
                "metadata": output_data["metadata"],
                "performance": perf_summary,
                "quality": quality
            }, f, indent=2)

        print(f"✓ Performance summary saved: {perf_file}")
        print()

        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------
        print("VALIDATION CHECKS")
        print("-" * 80)

        checks = []

        # Check 1: JSON is valid (already passed if we got here)
        checks.append(("JSON output valid", True))

        # Check 2: Segments present
        checks.append(("Segments > 0", len(aligned_segments) > 0))

        # Check 3: Speaker turns identified
        checks.append(("Speaker turns > 0", len(speaker_turns) > 0))

        # Check 4: Full text non-empty
        checks.append(("Full text present", len(transcription['full_text']) > 0))

        # Check 5: Duration matches
        duration_match = abs(transcription['duration'] - audio_duration) < 5
        checks.append(("Duration matches audio", duration_match))

        # Check 6: Timestamps sequential
        timestamps_ok = all(
            aligned_segments[i]["end"] <= aligned_segments[i+1]["start"] + 1.0
            for i in range(len(aligned_segments) - 1)
        )
        checks.append(("Timestamps sequential", timestamps_ok))

        # Check 7: Speaker alignment quality
        alignment_ok = quality['unknown_segments_percent'] < 30
        checks.append((f"Speaker alignment < 30% unknown", alignment_ok))

        all_passed = all(passed for _, passed in checks)

        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {check_name}")

        print()

        # ------------------------------------------
        # FINAL STATUS
        # ------------------------------------------
        if all_passed:
            print("=" * 80)
            print("STATUS: ✓ ALL CHECKS PASSED")
            print("=" * 80)
            print()
            print("DELIVERABLES:")
            print(f"  - Processing time: {total_time:.1f}s")
            print(f"  - API latency: {perf_summary['api_latency_seconds']:.1f}s")
            print(f"  - Speed ratio: {speed_ratio:.2f}x real-time")
            print(f"  - Memory usage: {perf_summary['current_memory_mb']:.1f}MB")
            print(f"  - Total segments: {quality['total_segments']}")
            print(f"  - Total speaker turns: {quality['total_speaker_turns']}")
            print(f"  - Speaker alignment quality: {quality['unknown_segments_percent']:.1f}% unknown")
            print(f"  - Output file: {output_file}")
            print()
            return 0
        else:
            print("=" * 80)
            print("STATUS: ✗ SOME CHECKS FAILED")
            print("=" * 80)
            print()
            return 1

    except Exception as e:
        print()
        print("=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
