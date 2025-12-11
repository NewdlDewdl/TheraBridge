#!/usr/bin/env python3
"""
Improved speaker alignment algorithm with multiple strategies:
1. Adjustable overlap threshold
2. Nearest-neighbor fallback
3. Interpolation for small gaps
4. Diagnostic metrics logging
"""

from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def align_speakers_with_segments_improved(
    segments: List[Dict],
    turns: List[Dict],
    overlap_threshold: float = 0.3,  # Reduced from 0.5
    use_nearest_fallback: bool = True,
    interpolate_gaps: bool = True,
    max_gap_for_interpolation: float = 2.0,  # Max gap in seconds
    verbose: bool = False
) -> Tuple[List[Dict], Dict]:
    """
    Improved alignment algorithm with multiple strategies to reduce Unknown speakers.

    Args:
        segments: List of transcription segments (with text, start, end)
        turns: List of speaker turns (with speaker, start, end)
        overlap_threshold: Minimum overlap percentage to assign speaker (default 30%)
        use_nearest_fallback: Use nearest speaker when overlap is insufficient
        interpolate_gaps: Interpolate speaker for small gaps between same speakers
        max_gap_for_interpolation: Maximum gap size for interpolation (seconds)
        verbose: Log detailed diagnostic information

    Returns:
        Tuple of (aligned_segments, metrics_dict)
    """

    aligned = []
    metrics = {
        'total_segments': len(segments),
        'unknown_segments': 0,
        'low_overlap_segments': 0,
        'nearest_neighbor_assigns': 0,
        'interpolated_assigns': 0,
        'overlap_distribution': defaultdict(int),  # Track overlap percentages
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
        overlaps = []

        for turn in turns:
            turn_start, turn_end = turn['start'], turn['end']

            # Calculate overlap
            overlap_start = max(seg_start, turn_start)
            overlap_end = min(seg_end, turn_end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > 0:
                overlap_pct = (overlap / seg_duration * 100) if seg_duration > 0 else 0
                overlaps.append((turn['speaker'], overlap, overlap_pct))

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_overlap_pct = overlap_pct / 100  # Convert to decimal
                    best_speaker = turn['speaker']

        # Track overlap distribution
        if best_overlap_pct > 0:
            bucket = int(best_overlap_pct * 10) * 10  # Round to nearest 10%
            metrics['overlap_distribution'][bucket] += 1

        # Step 2: Check if overlap meets threshold
        if best_overlap_pct < overlap_threshold:
            metrics['low_overlap_segments'] += 1

            # Step 3: Try nearest neighbor fallback
            if use_nearest_fallback and seg_duration > 0:
                nearest_speaker, nearest_distance = find_nearest_speaker(
                    seg_start, seg_end, turns
                )

                if nearest_speaker and nearest_distance < seg_duration:
                    best_speaker = nearest_speaker
                    metrics['nearest_neighbor_assigns'] += 1

                    if verbose:
                        logger.info(
                            f"Segment [{seg_start:.1f}s-{seg_end:.1f}s]: "
                            f"Using nearest neighbor {nearest_speaker} "
                            f"(distance: {nearest_distance:.1f}s, overlap: {best_overlap_pct*100:.1f}%)"
                        )

            # Step 4: Try interpolation for gaps
            if interpolate_gaps and best_speaker == "UNKNOWN":
                interpolated_speaker = try_interpolation(
                    seg_start, seg_end, turns, max_gap_for_interpolation
                )

                if interpolated_speaker:
                    best_speaker = interpolated_speaker
                    metrics['interpolated_assigns'] += 1

                    if verbose:
                        logger.info(
                            f"Segment [{seg_start:.1f}s-{seg_end:.1f}s]: "
                            f"Interpolated speaker {interpolated_speaker}"
                        )

        # Track Unknown segments
        if best_speaker == "UNKNOWN":
            metrics['unknown_segments'] += 1
            metrics['unknown_duration'] += seg_duration

            if verbose:
                logger.warning(
                    f"Segment [{seg_start:.1f}s-{seg_end:.1f}s] remains UNKNOWN: "
                    f"'{seg.get('text', '')[:50]}...'"
                )

        # Add aligned segment
        aligned.append({
            **seg,
            'speaker': best_speaker,
            'overlap_percentage': best_overlap_pct * 100,
            'alignment_method': get_alignment_method(
                best_speaker, best_overlap_pct, overlap_threshold,
                metrics['nearest_neighbor_assigns'], metrics['interpolated_assigns']
            )
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
    """
    Find the nearest speaker turn to a segment.

    Returns:
        Tuple of (speaker_name, distance_in_seconds)
    """
    min_distance = float('inf')
    nearest_speaker = None

    for turn in turns:
        # Calculate distance to nearest edge of turn
        if seg_end < turn['start']:
            # Segment is before turn
            distance = turn['start'] - seg_end
        elif seg_start > turn['end']:
            # Segment is after turn
            distance = seg_start - turn['end']
        else:
            # Segment overlaps with turn (shouldn't happen if we're here)
            distance = 0

        if distance < min_distance:
            min_distance = distance
            nearest_speaker = turn['speaker']

    return nearest_speaker, min_distance


def try_interpolation(
    seg_start: float,
    seg_end: float,
    turns: List[Dict],
    max_gap: float
) -> Optional[str]:
    """
    Try to interpolate speaker for segments in small gaps.

    If a segment falls in a gap between two turns of the SAME speaker,
    and the gap is small enough, assign that speaker.

    Returns:
        Speaker name if interpolation successful, None otherwise
    """
    # Find turns just before and after this segment
    turn_before = None
    turn_after = None

    for turn in turns:
        if turn['end'] <= seg_start:
            # Turn ends before or at segment start
            if not turn_before or turn['end'] > turn_before['end']:
                turn_before = turn
        elif turn['start'] >= seg_end:
            # Turn starts at or after segment end
            if not turn_after or turn['start'] < turn_after['start']:
                turn_after = turn

    # Check if we can interpolate
    if turn_before and turn_after:
        # Check if same speaker
        if turn_before['speaker'] == turn_after['speaker']:
            # Check gap size
            gap = turn_after['start'] - turn_before['end']
            if gap <= max_gap:
                return turn_before['speaker']

    return None


def get_alignment_method(
    speaker: str,
    overlap_pct: float,
    threshold: float,
    nn_count: int,
    interp_count: int
) -> str:
    """Determine which method was used for alignment"""
    if speaker == "UNKNOWN":
        return "none"
    elif overlap_pct >= threshold:
        return "overlap"
    elif nn_count > 0:
        return "nearest_neighbor"
    elif interp_count > 0:
        return "interpolation"
    else:
        return "unknown"


def print_alignment_metrics(metrics: Dict) -> None:
    """Pretty print alignment metrics"""
    print("\n" + "="*60)
    print("ALIGNMENT METRICS")
    print("="*60)

    print(f"\nTotal segments: {metrics['total_segments']}")
    print(f"Unknown segments: {metrics['unknown_segments']} ({metrics['unknown_percentage']:.1f}%)")
    print(f"Total duration: {metrics['total_duration']:.1f}s")
    print(f"Unknown duration: {metrics['unknown_duration']:.1f}s ({metrics['unknown_duration_percentage']:.1f}%)")

    print(f"\nAlignment methods used:")
    print(f"  Low overlap segments: {metrics['low_overlap_segments']}")
    print(f"  Nearest neighbor assigns: {metrics['nearest_neighbor_assigns']}")
    print(f"  Interpolated assigns: {metrics['interpolated_assigns']}")

    print(f"\nOverlap distribution:")
    for pct in sorted(metrics['overlap_distribution'].keys()):
        count = metrics['overlap_distribution'][pct]
        print(f"  {pct}-{pct+10}%: {count} segments")

    print("="*60)


if __name__ == "__main__":
    # Test with existing data
    import json
    import sys

    json_path = "tests/outputs/diarization_output.json"

    if len(sys.argv) > 1:
        json_path = sys.argv[1]

    print(f"Testing improved alignment on: {json_path}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Get the original segments (before diarization)
    segments = []

    # Extract segments from diarized_segments (they contain the original timing)
    for seg in data.get('diarized_segments', []):
        segments.append({
            'text': seg.get('text', ''),
            'start': seg.get('start', 0),
            'end': seg.get('end', 0)
        })

    speaker_turns = data.get('speaker_turns', [])

    if not segments:
        print("No segments found in file")
        sys.exit(1)

    # Test with different configurations
    configs = [
        {"overlap_threshold": 0.5, "use_nearest_fallback": False, "interpolate_gaps": False},
        {"overlap_threshold": 0.3, "use_nearest_fallback": False, "interpolate_gaps": False},
        {"overlap_threshold": 0.3, "use_nearest_fallback": True, "interpolate_gaps": False},
        {"overlap_threshold": 0.3, "use_nearest_fallback": True, "interpolate_gaps": True},
    ]

    for i, config in enumerate(configs, 1):
        print(f"\n\nConfiguration {i}: {config}")
        aligned, metrics = align_speakers_with_segments_improved(
            segments,
            speaker_turns,
            **config,
            verbose=False
        )
        print_alignment_metrics(metrics)

        # Show improvement
        original_unknown = len([s for s in data.get('diarized_segments', []) if s.get('speaker') == 'UNKNOWN'])
        new_unknown = metrics['unknown_segments']
        if original_unknown > 0:
            improvement = (original_unknown - new_unknown) / original_unknown * 100
            print(f"\n✅ Improvement: Reduced Unknown segments from {original_unknown} to {new_unknown} ({improvement:.1f}% reduction)")