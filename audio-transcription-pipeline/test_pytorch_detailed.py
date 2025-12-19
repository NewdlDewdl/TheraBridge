#!/usr/bin/env python3
"""
Detailed PyTorch and CUDA Capabilities Test
Tests all PyTorch backends and capabilities
"""

import sys

def test_torch_import():
    """Test PyTorch import"""
    print("=" * 70)
    print("PyTorch Import Test")
    print("=" * 70)
    try:
        import torch
        print(f"✓ PyTorch imported successfully")
        print(f"  Version: {torch.__version__}")
        return torch
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return None

def test_cuda_detailed(torch):
    """Detailed CUDA tests"""
    print("\n" + "=" * 70)
    print("CUDA Detailed Analysis")
    print("=" * 70)

    print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")
    print(f"torch.cuda.device_count(): {torch.cuda.device_count()}")

    if hasattr(torch.version, 'cuda'):
        print(f"torch.version.cuda: {torch.version.cuda}")
    else:
        print(f"torch.version.cuda: None (CPU-only build)")

    if torch.cuda.is_available():
        print("\nCUDA Device Details:")
        for i in range(torch.cuda.device_count()):
            print(f"\nDevice {i}:")
            print(f"  Name: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"  Total memory: {props.total_memory / 1024**3:.2f} GB")
            print(f"  Major: {props.major}")
            print(f"  Minor: {props.minor}")
            print(f"  Multi-processor count: {props.multi_processor_count}")

        # Test tensor creation on CUDA
        try:
            print("\nTensor creation test:")
            x = torch.randn(10, 10).cuda()
            print(f"✓ Created tensor on CUDA: {x.device}")
            del x
        except Exception as e:
            print(f"✗ CUDA tensor creation failed: {e}")
    else:
        print("\nNo CUDA devices available")
        print("Reasons could be:")
        print("  1. No NVIDIA GPU in system")
        print("  2. CUDA drivers not installed")
        print("  3. PyTorch built without CUDA support")

def test_mps_detailed(torch):
    """Detailed MPS (Apple Silicon) tests"""
    print("\n" + "=" * 70)
    print("MPS (Apple Silicon) Detailed Analysis")
    print("=" * 70)

    has_mps_backend = hasattr(torch.backends, 'mps')
    print(f"torch.backends.mps exists: {has_mps_backend}")

    if has_mps_backend:
        mps_available = torch.backends.mps.is_available()
        print(f"torch.backends.mps.is_available(): {mps_available}")

        mps_built = torch.backends.mps.is_built()
        print(f"torch.backends.mps.is_built(): {mps_built}")

        if mps_available:
            print("\nMPS Device Test:")
            try:
                # Test tensor creation on MPS
                x = torch.randn(10, 10, device='mps')
                print(f"✓ Created tensor on MPS: {x.device}")

                # Test basic operation
                y = x @ x.T
                print(f"✓ Matrix multiplication on MPS successful")
                print(f"  Result shape: {y.shape}")
                del x, y
            except Exception as e:
                print(f"✗ MPS tensor operation failed: {e}")
        else:
            print("\nMPS not available on this system")
    else:
        print("\nMPS backend not present (non-Apple Silicon system)")

def test_cpu_operations(torch):
    """Test CPU operations"""
    print("\n" + "=" * 70)
    print("CPU Operations Test")
    print("=" * 70)

    try:
        # Basic tensor operations
        x = torch.randn(100, 100)
        y = torch.randn(100, 100)
        z = x @ y
        print(f"✓ Matrix multiplication on CPU successful")
        print(f"  Input shape: {x.shape}")
        print(f"  Output shape: {z.shape}")

        # Test autograd
        x.requires_grad = True
        y.requires_grad = True
        loss = (x @ y).sum()
        loss.backward()
        print(f"✓ Autograd backward pass successful")
        print(f"  Gradient shape: {x.grad.shape}")

    except Exception as e:
        print(f"✗ CPU operations failed: {e}")
        import traceback
        traceback.print_exc()

def test_backend_preferences(torch):
    """Test backend preferences and capabilities"""
    print("\n" + "=" * 70)
    print("Backend Preferences")
    print("=" * 70)

    backends = []

    if torch.cuda.is_available():
        backends.append(("CUDA", "cuda", "Best for NVIDIA GPUs"))

    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        backends.append(("MPS", "mps", "Apple Silicon GPU (limited ML framework support)"))

    backends.append(("CPU", "cpu", "Universal fallback"))

    print("Available compute backends (in priority order):")
    for i, (name, device, desc) in enumerate(backends, 1):
        print(f"  {i}. {name} ('{device}'): {desc}")

    print(f"\nRecommended device for this system: {backends[0][1]}")

    return backends

def test_whisper_compatibility(torch):
    """Test compatibility with Whisper models"""
    print("\n" + "=" * 70)
    print("Whisper Model Compatibility")
    print("=" * 70)

    # Whisper requires specific PyTorch features
    print("Checking Whisper requirements:")

    # Check if FFT operations work (required for audio processing)
    try:
        x = torch.randn(1, 16000)  # 1 second of audio at 16kHz
        fft = torch.fft.rfft(x)
        print(f"✓ FFT operations supported (required for audio processing)")
    except Exception as e:
        print(f"✗ FFT operations failed: {e}")

    # Check convolution support
    try:
        conv = torch.nn.Conv1d(1, 32, kernel_size=3)
        x = torch.randn(1, 1, 100)
        out = conv(x)
        print(f"✓ Convolution operations supported (required for neural networks)")
    except Exception as e:
        print(f"✗ Convolution operations failed: {e}")

    # Check attention mechanism
    try:
        attn = torch.nn.MultiheadAttention(embed_dim=256, num_heads=8)
        x = torch.randn(10, 1, 256)
        out, _ = attn(x, x, x)
        print(f"✓ Attention mechanisms supported (required for Transformer models)")
    except Exception as e:
        print(f"✗ Attention mechanisms failed: {e}")

def generate_summary(torch, backends):
    """Generate final summary"""
    print("\n" + "=" * 70)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 70)

    # Determine best pipeline
    if torch.cuda.is_available():
        print("\n🎯 Recommended Pipeline: GPU-accelerated (pipeline_gpu.py)")
        print("   Reason: NVIDIA GPU with CUDA available")
        print("   Expected speedup: 10-50x vs CPU")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("\n🎯 Recommended Pipeline: CPU/API-based (pipeline.py)")
        print("   Reason: Apple Silicon MPS available but not fully supported by Whisper")
        print("   Note: Use OpenAI Whisper API for best performance")
    else:
        print("\n🎯 Recommended Pipeline: CPU/API-based (pipeline.py)")
        print("   Reason: No GPU acceleration available")
        print("   Note: Use OpenAI Whisper API for best performance")

    # Environment variable check
    print("\n📋 Required Environment Variables:")
    import os
    openai_key = os.environ.get('OPENAI_API_KEY')
    hf_token = os.environ.get('HF_TOKEN')

    print(f"   OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set (required for API-based transcription)'}")
    print(f"   HF_TOKEN: {'✓ Set' if hf_token else '✗ Not set (required for speaker diarization)'}")

    # Quick start command
    print("\n🚀 Quick Start Command:")
    if torch.cuda.is_available():
        print("   cd audio-transcription-pipeline")
        print("   source venv/bin/activate")
        print("   python tests/test_full_pipeline.py  # GPU-accelerated")
    else:
        print("   cd audio-transcription-pipeline")
        print("   source venv/bin/activate")
        print("   python tests/test_full_pipeline.py  # CPU/API-based")

if __name__ == "__main__":
    print("\n🔬 Detailed PyTorch Capabilities Test\n")

    # Load .env
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    # Run tests
    torch = test_torch_import()
    if torch is None:
        sys.exit(1)

    test_cuda_detailed(torch)
    test_mps_detailed(torch)
    test_cpu_operations(torch)
    backends = test_backend_preferences(torch)
    test_whisper_compatibility(torch)
    generate_summary(torch, backends)

    print("\n✅ All tests completed\n")
