#!/usr/bin/env python3
"""
Diagnostic script to analyze "Unknown" speaker labels in diarization output.
Based on the diagnostic XML prompt to identify root causes and test solutions.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def load_diarization_output(json_path: str) -> Dict:
    """Load the diarization JSON output"""
    with open(json_path, 'r') as f:
        return json.load(f)

def analyze_unknown_segments(data: Dict) -> None:
    """Detailed analysis of Unknown speaker segments"""

    print("="*70)
    print("UNKNOWN SPEAKER SEGMENT ANALYSIS")
    print("="*70)
    print()

    segments = data.get('diarized_segments', [])
    speaker_turns = data.get('speaker_turns', [])
    metadata = data.get('metadata', {})

    # 1. Basic Statistics
    print("1. BASIC STATISTICS")
    print("-"*50)

    total_segments = len(segments)
    unknown_segments = [s for s in segments if s.get('speaker') == 'UNKNOWN']
    unknown_count = len(unknown_segments)
    unknown_percentage = (unknown_count / total_segments * 100) if total_segments > 0 else 0

    print(f"Total segments: {total_segments}")
    print(f"Unknown segments: {unknown_count} ({unknown_percentage:.1f}%)")
    print()

    # Calculate duration statistics
    total_duration = sum(s['end'] - s['start'] for s in segments)
    unknown_duration = sum(s['end'] - s['start'] for s in unknown_segments)
    unknown_duration_pct = (unknown_duration / total_duration * 100) if total_duration > 0 else 0

    print(f"Total audio duration: {total_duration:.1f}s")
    print(f"Unknown speaker duration: {unknown_duration:.1f}s ({unknown_duration_pct:.1f}%)")
    print()

    # 2. Timeline Analysis
    print("2. TIMELINE ANALYSIS - Where do Unknown segments occur?")
    print("-"*50)

    if unknown_segments:
        first_unknown = unknown_segments[0]
        last_unknown = unknown_segments[-1]

        print(f"First Unknown segment: {first_unknown['start']:.1f}s - {first_unknown['end']:.1f}s")
        print(f"Last Unknown segment: {last_unknown['start']:.1f}s - {last_unknown['end']:.1f}s")
        print()

        # Check for patterns
        print("Unknown segment distribution:")

        # Group by time periods (beginning, middle, end)
        recording_duration = metadata.get('duration', 0)
        beginning_threshold = recording_duration * 0.1  # First 10%
        end_threshold = recording_duration * 0.9  # Last 10%

        beginning_unknowns = [s for s in unknown_segments if s['start'] < beginning_threshold]
        middle_unknowns = [s for s in unknown_segments if beginning_threshold <= s['start'] < end_threshold]
        end_unknowns = [s for s in unknown_segments if s['start'] >= end_threshold]

        print(f"  Beginning (0-10%): {len(beginning_unknowns)} segments")
        print(f"  Middle (10-90%): {len(middle_unknowns)} segments")
        print(f"  End (90-100%): {len(end_unknowns)} segments")
        print()

    # 3. Gap Analysis
    print("3. DIARIZATION GAP ANALYSIS")
    print("-"*50)

    if speaker_turns:
        first_turn_start = speaker_turns[0]['start']
        last_turn_end = speaker_turns[-1]['end']

        print(f"First speaker turn starts at: {first_turn_start:.1f}s")
        print(f"Last speaker turn ends at: {last_turn_end:.1f}s")
        print()

        # Check for gaps at beginning
        if first_turn_start > 0:
            print(f"⚠️  GAP: No speaker detected for first {first_turn_start:.1f}s")

            # Count segments in this gap
            gap_segments = [s for s in segments if s['end'] <= first_turn_start]
            print(f"   Segments in gap: {len(gap_segments)}")
            for seg in gap_segments[:3]:  # Show first 3
                print(f"     [{seg['start']:.1f}s-{seg['end']:.1f}s]: \"{seg['text'][:50]}...\"")

        print()

        # Find gaps between speaker turns
        gaps = []
        for i in range(len(speaker_turns) - 1):
            gap_start = speaker_turns[i]['end']
            gap_end = speaker_turns[i+1]['start']
            if gap_end - gap_start > 0.5:  # Significant gap (>0.5s)
                gaps.append((gap_start, gap_end))

        if gaps:
            print(f"Found {len(gaps)} significant gaps (>0.5s) between speaker turns:")
            for i, (start, end) in enumerate(gaps[:5]):  # Show first 5
                duration = end - start
                print(f"  Gap {i+1}: {start:.1f}s - {end:.1f}s (duration: {duration:.1f}s)")
        print()

    # 4. Overlap Analysis for Unknown Segments
    print("4. OVERLAP ANALYSIS FOR UNKNOWN SEGMENTS")
    print("-"*50)

    if unknown_segments[:5]:  # Analyze first 5 unknown segments
        print("Analyzing first 5 Unknown segments:")
        print()

        for i, seg in enumerate(unknown_segments[:5]):
            seg_start, seg_end = seg['start'], seg['end']
            seg_duration = seg_end - seg_start

            print(f"Unknown Segment {i+1}: [{seg_start:.1f}s - {seg_end:.1f}s] duration: {seg_duration:.1f}s")
            print(f"  Text: \"{seg['text'][:60]}...\"")

            # Find overlapping speaker turns
            overlaps = []
            for turn in speaker_turns:
                overlap_start = max(seg_start, turn['start'])
                overlap_end = min(seg_end, turn['end'])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > 0:
                    overlap_pct = (overlap / seg_duration * 100) if seg_duration > 0 else 0
                    overlaps.append((turn['speaker'], overlap, overlap_pct))

            if overlaps:
                print("  Overlaps with speaker turns:")
                for speaker, overlap, pct in overlaps:
                    print(f"    {speaker}: {overlap:.2f}s ({pct:.1f}% of segment)")
            else:
                print("  ⚠️  NO OVERLAP with any speaker turn")

            # Find nearest speaker turn
            min_distance = float('inf')
            nearest_speaker = None
            for turn in speaker_turns:
                # Distance to nearest edge of turn
                distance = min(abs(seg_start - turn['end']), abs(seg_end - turn['start']))
                if distance < min_distance:
                    min_distance = distance
                    nearest_speaker = turn['speaker']

            if nearest_speaker:
                print(f"  Nearest speaker: {nearest_speaker} (distance: {min_distance:.1f}s)")
            print()

    # 5. Test Different Thresholds
    print("5. TESTING DIFFERENT OVERLAP THRESHOLDS")
    print("-"*50)

    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]

    for threshold in thresholds:
        would_be_unknown = 0

        for seg in segments:
            seg_start, seg_end = seg['start'], seg['end']
            seg_duration = seg_end - seg_start

            best_overlap = 0
            for turn in speaker_turns:
                overlap_start = max(seg_start, turn['start'])
                overlap_end = min(seg_end, turn['end'])
                overlap = max(0, overlap_end - overlap_start)
                best_overlap = max(best_overlap, overlap)

            if seg_duration > 0 and (best_overlap / seg_duration) < threshold:
                would_be_unknown += 1

        unknown_pct = (would_be_unknown / total_segments * 100) if total_segments > 0 else 0
        print(f"Threshold {threshold*100:.0f}%: {would_be_unknown} segments would be Unknown ({unknown_pct:.1f}%)")

    print()

    # 6. Recommendations
    print("6. RECOMMENDATIONS")
    print("-"*50)

    if first_turn_start > 2.0:
        print("🔧 Recommendation 1: Handle intro/non-speech audio")
        print("   The first speaker turn starts late. Consider:")
        print("   - Pre-processing to skip intro music/silence")
        print("   - Using VAD to filter non-speech segments")
        print()

    if unknown_percentage > 10:
        print("🔧 Recommendation 2: Lower overlap threshold")
        print("   High percentage of Unknown segments. Consider:")
        print("   - Reducing threshold from 50% to 30%")
        print("   - Implementing nearest-neighbor fallback")
        print()

    if gaps:
        print("🔧 Recommendation 3: Handle diarization gaps")
        print("   Multiple gaps in speaker detection. Consider:")
        print("   - Interpolating speakers across small gaps")
        print("   - Using previous/next speaker for isolated Unknown segments")
        print()

    print("="*70)

def main():
    # Default to the test output file
    json_path = "tests/outputs/diarization_output.json"

    if len(sys.argv) > 1:
        json_path = sys.argv[1]

    if not Path(json_path).exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    print(f"Loading diarization output from: {json_path}")
    print()

    data = load_diarization_output(json_path)
    analyze_unknown_segments(data)

if __name__ == "__main__":
    main()