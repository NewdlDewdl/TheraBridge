#!/usr/bin/env python3
"""
Main entry point for Colab L4 GPU pipeline
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pipeline_colab import ColabTranscriptionPipeline


def main():
    parser = argparse.ArgumentParser(description="Colab L4 GPU Audio Transcription")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--num-speakers", type=int, default=2, help="Number of speakers")
    parser.add_argument("--language", default="en", help="Language code")
    parser.add_argument("--output", default="/content/transcription.json", help="Output file")
    parser.add_argument("--whisper-model", default="large-v3", help="Whisper model size")

    args = parser.parse_args()

    # Verify file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found: {args.audio_file}")
        sys.exit(1)

    # Initialize pipeline
    print("Initializing Colab L4 pipeline...")
    pipeline = ColabTranscriptionPipeline(
        whisper_model=args.whisper_model,
        device="cuda",
        compute_type="float16"
    )

    # Process audio
    print(f"Processing: {args.audio_file}")
    result = pipeline.process(
        args.audio_file,
        num_speakers=args.num_speakers,
        language=args.language
    )

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"Results saved to: {output_path}")

    # Print summary
    print("\n" + "="*50)
    print("TRANSCRIPTION SUMMARY")
    print("="*50)
    print(f"Duration: {result['duration']:.1f} seconds")
    print(f"Segments: {len(result['segments'])}")
    print(f"Speakers: {args.num_speakers}")
    print(f"Processing time: {result['performance_metrics']['total_duration']:.1f}s")

    # Calculate speedup
    speedup = result['duration'] / result['performance_metrics']['total_duration']
    print(f"Real-time factor: {speedup:.2f}x")

    return 0


if __name__ == "__main__":
    sys.exit(main())