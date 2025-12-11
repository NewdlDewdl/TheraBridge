#!/usr/bin/env python3
"""
GPU-Accelerated Transcription CLI
Works on Vast.ai, RunPod, Lambda Labs, Paperspace, Google Colab
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="GPU-accelerated audio transcription with speaker diarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s audio.mp3
  %(prog)s audio.mp3 --speakers 2 --output results/
  %(prog)s audio.mp3 --model medium --no-diarization
  %(prog)s audio.mp3 --language es --speakers 3

Requirements:
  - NVIDIA GPU with CUDA support
  - HF_TOKEN environment variable (for diarization)

Get HuggingFace token: https://huggingface.co/settings/tokens
        """
    )

    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--speakers", type=int, default=2,
                        help="Number of speakers (default: 2)")
    parser.add_argument("--model", default="large-v3",
                        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
                        help="Whisper model size (default: large-v3)")
    parser.add_argument("--language", default="en",
                        help="Language code (default: en)")
    parser.add_argument("--output", default=".",
                        help="Output directory (default: current directory)")
    parser.add_argument("--no-diarization", action="store_true",
                        help="Disable speaker diarization")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Validate audio file
    if not os.path.exists(args.audio_file):
        print(f"ERROR: Audio file not found: {args.audio_file}")
        sys.exit(1)

    # Setup
    from src.pipeline_gpu import GPUTranscriptionPipeline

    # Process
    try:
        pipeline = GPUTranscriptionPipeline(whisper_model=args.model)
        result = pipeline.process(
            args.audio_file,
            num_speakers=args.speakers,
            language=args.language,
            enable_diarization=not args.no_diarization
        )

        # Save output
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"transcription_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\nResults saved to: {output_file}")

        # Print summary
        if args.verbose:
            print("\n" + "="*60)
            print("Transcription Summary")
            print("="*60)
            print(result['full_text'])
            print("="*60)

        return 0

    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
