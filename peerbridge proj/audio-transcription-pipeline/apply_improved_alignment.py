#!/usr/bin/env python3
"""
Apply the improved alignment algorithm to existing diarization output.
This script reads the existing diarization_output.json and re-aligns it with better strategies.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

def align_speakers_with_segments_improved(
    segments: List[Dict],
    turns: List[Dict],
    overlap_threshold: float = 0.3,
    use_nearest_fallback: bool = True,
    interpolate_gaps: bool = True,
    max_gap_for_interpolation: float = 2.0
) -> Tuple[List[Dict], Dict]:
    """
    Improved alignment algorithm with multiple strategies to reduce Unknown speakers.
    """
    aligned = []
    metrics = {
        'total_segments': len(segments),
        'unknown_segments': 0,
        'low_overlap_segments': 0,
        'nearest_neighbor_assigns': 0,
        'interpolated_assigns': 0,
        'unknown_duration': 0.0,
        'total_duration': 0.0
    }

    for seg in segments:
        seg_start, seg_end = seg.get('start', 0), seg.get('end', 0)
        seg_duration = seg_end - seg_start
        metrics['total_duration'] += seg_duration

        # Step 1: Find best overlapping speaker
        best_speaker = "UNKNOWN"
        best_overlap = 0
        best_overlap_pct = 0

        for turn in turns:
            turn_start, turn_end = turn['start'], turn['end']

            # Calculate overlap
            overlap_start = max(seg_start, turn_start)
            overlap_end = min(seg_end, turn_end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_overlap_pct = (overlap / seg_duration) if seg_duration > 0 else 0
                best_speaker = turn['speaker']

        # Step 2: Check if overlap meets threshold
        if best_overlap_pct < overlap_threshold:
            metrics['low_overlap_segments'] += 1

            # Step 3: Try nearest neighbor fallback
            if use_nearest_fallback and seg_duration > 0:
                nearest_speaker, nearest_distance = find_nearest_speaker(seg_start, seg_end, turns)

                if nearest_speaker and nearest_distance < seg_duration:
                    best_speaker = nearest_speaker
                    metrics['nearest_neighbor_assigns'] += 1

            # Step 4: Try interpolation for gaps
            if interpolate_gaps and best_speaker == "UNKNOWN":
                interpolated_speaker = try_interpolation(seg_start, seg_end, turns, max_gap_for_interpolation)

                if interpolated_speaker:
                    best_speaker = interpolated_speaker
                    metrics['interpolated_assigns'] += 1

        # Track Unknown segments
        if best_speaker == "UNKNOWN":
            metrics['unknown_segments'] += 1
            metrics['unknown_duration'] += seg_duration

        # Add aligned segment
        aligned.append({
            **seg,
            'speaker': best_speaker,
            'overlap_percentage': best_overlap_pct * 100
        })

    # Calculate final metrics
    metrics['unknown_percentage'] = (
        metrics['unknown_segments'] / metrics['total_segments'] * 100
        if metrics['total_segments'] > 0 else 0
    )
    metrics['unknown_duration_percentage'] = (
        metrics['unknown_duration'] / metrics['total_duration'] * 100
        if metrics['total_duration'] > 0 else 0
    )

    return aligned, metrics

def find_nearest_speaker(seg_start: float, seg_end: float, turns: List[Dict]) -> Tuple[Optional[str], float]:
    """Find the nearest speaker turn to a segment"""
    min_distance = float('inf')
    nearest_speaker = None

    for turn in turns:
        if seg_end < turn['start']:
            distance = turn['start'] - seg_end
        elif seg_start > turn['end']:
            distance = seg_start - turn['end']
        else:
            distance = 0

        if distance < min_distance:
            min_distance = distance
            nearest_speaker = turn['speaker']

    return nearest_speaker, min_distance

def try_interpolation(seg_start: float, seg_end: float, turns: List[Dict], max_gap: float) -> Optional[str]:
    """Try to interpolate speaker for segments in small gaps"""
    turn_before = None
    turn_after = None

    for turn in turns:
        if turn['end'] <= seg_start:
            if not turn_before or turn['end'] > turn_before['end']:
                turn_before = turn
        elif turn['start'] >= seg_end:
            if not turn_after or turn['start'] < turn_after['start']:
                turn_after = turn

    if turn_before and turn_after:
        if turn_before['speaker'] == turn_after['speaker']:
            gap = turn_after['start'] - turn_before['end']
            if gap <= max_gap:
                return turn_before['speaker']

    return None

def main():
    # Load existing diarization output
    input_json = "tests/outputs/diarization_output.json"
    output_json = "tests/outputs/diarization_output_improved.json"

    print("="*60)
    print("APPLYING IMPROVED ALIGNMENT TO EXISTING DATA")
    print("="*60)
    print()

    # Load data
    with open(input_json, 'r') as f:
        data = json.load(f)

    # Extract segments and speaker turns
    original_segments = data.get('diarized_segments', [])
    speaker_turns = data.get('speaker_turns', [])

    # Extract just the timing and text from original segments (remove old speaker assignments)
    segments = []
    for seg in original_segments:
        segments.append({
            'text': seg.get('text', ''),
            'start': seg.get('start', 0),
            'end': seg.get('end', 0)
        })

    print(f"Loaded {len(segments)} segments and {len(speaker_turns)} speaker turns")
    print()

    # Count original Unknown segments
    original_unknown = len([s for s in original_segments if s.get('speaker') == 'UNKNOWN'])
    print(f"Original Unknown segments: {original_unknown} ({original_unknown/len(segments)*100:.1f}%)")
    print()

    # Apply improved alignment
    print("Applying improved alignment...")
    print("  - Overlap threshold: 30% (reduced from 50%)")
    print("  - Using nearest-neighbor fallback")
    print("  - Using interpolation for small gaps")
    print()

    aligned_segments, metrics = align_speakers_with_segments_improved(
        segments,
        speaker_turns,
        overlap_threshold=0.3,
        use_nearest_fallback=True,
        interpolate_gaps=True,
        max_gap_for_interpolation=2.0
    )

    # Print results
    print("RESULTS:")
    print("-"*40)
    print(f"Total segments: {metrics['total_segments']}")
    print(f"Unknown segments: {metrics['unknown_segments']} ({metrics['unknown_percentage']:.1f}%)")
    print(f"Low overlap segments: {metrics['low_overlap_segments']}")
    print(f"Nearest neighbor assigns: {metrics['nearest_neighbor_assigns']}")
    print(f"Interpolated assigns: {metrics['interpolated_assigns']}")
    print()

    # Calculate improvement
    if original_unknown > 0:
        reduction = original_unknown - metrics['unknown_segments']
        reduction_pct = (reduction / original_unknown) * 100
        print(f"✅ IMPROVEMENT: Reduced Unknown segments by {reduction} ({reduction_pct:.1f}% reduction)")
    else:
        print("✅ No Unknown segments to improve")
    print()

    # Save improved output
    improved_data = {
        **data,  # Keep all original metadata
        'diarized_segments': aligned_segments,
        'alignment_metrics': metrics,
        'alignment_config': {
            'overlap_threshold': 0.3,
            'use_nearest_fallback': True,
            'interpolate_gaps': True,
            'max_gap_for_interpolation': 2.0
        }
    }

    with open(output_json, 'w') as f:
        json.dump(improved_data, f, indent=2)

    print(f"Saved improved alignment to: {output_json}")
    print()

    # Show sample of improved segments
    print("Sample of improved segments:")
    print("-"*60)
    for i, seg in enumerate(aligned_segments[:5]):
        speaker = seg['speaker']
        text = seg['text'][:50] + "..." if len(seg['text']) > 50 else seg['text']
        start = seg['start']
        end = seg['end']
        overlap = seg.get('overlap_percentage', 0)
        print(f"{i+1}. [{start:.1f}s - {end:.1f}s] {speaker} (overlap: {overlap:.1f}%)")
        print(f"   \"{text}\"")
        print()

    print("="*60)
    print("✅ COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()