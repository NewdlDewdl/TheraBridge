#!/usr/bin/env python3
"""
Test script for Colab L4 GPU acceleration
"""

import os
import sys
import time
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_gpu_availability():
    """Test GPU detection and properties"""
    print("Testing GPU availability...")
    assert torch.cuda.is_available(), "CUDA not available"

    device_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3

    print(f"✓ GPU detected: {device_name}")
    print(f"✓ VRAM: {vram:.1f} GB")

    # Verify L4 GPU (should have 24GB VRAM)
    assert "L4" in device_name or vram > 20, f"Expected L4 GPU, got {device_name}"
    print("✓ L4 GPU confirmed")


def test_gpu_audio_ops():
    """Test GPU audio operations"""
    print("\nTesting GPU audio operations...")
    from gpu_audio_ops import GPUAudioProcessor

    processor = GPUAudioProcessor()

    # Create test audio tensor
    sample_rate = 16000
    duration = 10  # seconds
    waveform = torch.randn(1, sample_rate * duration).to(processor.device)

    # Test silence detection
    start = time.perf_counter()
    silence_mask, regions = processor.detect_silence_gpu(waveform, sample_rate=sample_rate)
    silence_time = time.perf_counter() - start
    print(f"✓ Silence detection: {silence_time*1000:.2f}ms")

    # Test normalization
    start = time.perf_counter()
    normalized = processor.normalize_gpu(waveform)
    norm_time = time.perf_counter() - start
    print(f"✓ Normalization: {norm_time*1000:.2f}ms")

    # Test resampling
    start = time.perf_counter()
    resampled = processor.resample_gpu(waveform, 16000, 8000)
    resample_time = time.perf_counter() - start
    print(f"✓ Resampling: {resample_time*1000:.2f}ms")

    # Verify all operations stayed on GPU
    assert waveform.device.type == "cuda"
    assert normalized.device.type == "cuda"
    assert resampled.device.type == "cuda"
    print("✓ All operations on GPU")


def test_faster_whisper():
    """Test faster-whisper GPU support"""
    print("\nTesting faster-whisper...")
    from faster_whisper import WhisperModel

    # Load tiny model for testing
    model = WhisperModel("tiny", device="cuda", compute_type="float16")

    # Create test audio
    import numpy as np
    sample_rate = 16000
    duration = 5
    audio = np.random.randn(sample_rate * duration).astype(np.float32)

    # Test transcription
    start = time.perf_counter()
    segments, info = model.transcribe(audio)
    segments_list = list(segments)  # Force evaluation
    transcribe_time = time.perf_counter() - start

    print(f"✓ Transcription completed in {transcribe_time:.2f}s")
    print(f"✓ Detected language: {info.language}")
    print("✓ Faster-whisper GPU support confirmed")


def test_pipeline():
    """Test full pipeline"""
    print("\nTesting full pipeline...")
    from pipeline_colab import ColabTranscriptionPipeline

    # Initialize pipeline
    pipeline = ColabTranscriptionPipeline(
        whisper_model="tiny",  # Use tiny for testing
        device="cuda",
        compute_type="float16"
    )
    print("✓ Pipeline initialized")

    # Create test audio file
    import torchaudio
    sample_rate = 16000
    duration = 10
    waveform = torch.randn(1, sample_rate * duration)
    test_file = "/content/test_audio.wav"
    torchaudio.save(test_file, waveform, sample_rate)

    # Process
    result = pipeline.process(test_file, num_speakers=2, language="en")

    assert "segments" in result
    assert "performance_metrics" in result
    print(f"✓ Pipeline processed {len(result['segments'])} segments")
    print(f"✓ Total time: {result['performance_metrics']['total_duration']:.2f}s")

    # Cleanup
    os.remove(test_file)


def main():
    print("="*50)
    print("COLAB L4 GPU ACCELERATION TEST SUITE")
    print("="*50)

    try:
        test_gpu_availability()
        test_gpu_audio_ops()
        test_faster_whisper()
        test_pipeline()

        print("\n" + "="*50)
        print("ALL TESTS PASSED ✓")
        print("="*50)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())