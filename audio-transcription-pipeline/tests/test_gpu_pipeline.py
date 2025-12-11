#!/usr/bin/env python3
"""
End-to-end tests for GPU pipeline
"""

import os
import sys
import json
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline_gpu import GPUTranscriptionPipeline


class TestGPUPipeline(unittest.TestCase):
    """Test GPU transcription pipeline"""

    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        cls.test_audio = Path(__file__).parent / "samples" / "onemintestvid.mp3"

        if not cls.test_audio.exists():
            raise FileNotFoundError(f"Test audio not found: {cls.test_audio}")

        cls.output_dir = Path(__file__).parent / "outputs"
        cls.output_dir.mkdir(exist_ok=True)

    def test_pipeline_initialization(self):
        """Test that pipeline initializes correctly"""
        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")
        self.assertIsNotNone(pipeline.config)
        self.assertIsNotNone(pipeline.audio_processor)
        self.assertIsNotNone(pipeline.logger)

    def test_transcription_only(self):
        """Test transcription without diarization"""
        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")

        result = pipeline.process(
            str(self.test_audio),
            enable_diarization=False
        )

        # Verify result structure
        self.assertIn('segments', result)
        self.assertIn('full_text', result)
        self.assertIn('duration', result)
        self.assertGreater(len(result['segments']), 0)
        self.assertGreater(len(result['full_text']), 0)
        self.assertGreater(result['duration'], 0)

    def test_transcription_with_diarization(self):
        """Test full pipeline with diarization"""
        # Skip if HF_TOKEN not set
        if not os.getenv("HF_TOKEN"):
            self.skipTest("HF_TOKEN not set, skipping diarization test")

        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")

        result = pipeline.process(
            str(self.test_audio),
            num_speakers=2,
            enable_diarization=True
        )

        # Verify diarization results
        self.assertIn('aligned_segments', result)
        self.assertIn('speaker_turns', result)
        self.assertGreater(len(result['aligned_segments']), 0)

        # Check speaker labels
        speakers = set(seg['speaker'] for seg in result['aligned_segments'])
        self.assertGreater(len(speakers), 0)

    def test_performance_metrics(self):
        """Test that performance metrics are captured"""
        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")

        result = pipeline.process(
            str(self.test_audio),
            enable_diarization=False
        )

        # Verify performance metrics exist
        self.assertIn('performance_metrics', result)
        metrics = result['performance_metrics']
        self.assertIn('total_duration', metrics)
        self.assertIn('stages', metrics)
        self.assertGreater(metrics['total_duration'], 0)

    def test_output_save(self):
        """Test that results can be saved"""
        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")

        result = pipeline.process(
            str(self.test_audio),
            enable_diarization=False
        )

        # Save result
        output_file = self.output_dir / "test_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 0)

    def test_invalid_audio_file(self):
        """Test error handling for invalid audio"""
        pipeline = GPUTranscriptionPipeline(whisper_model="tiny")

        with self.assertRaises(FileNotFoundError):
            pipeline.process("nonexistent.mp3")


def main():
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
