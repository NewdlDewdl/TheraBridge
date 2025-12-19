#!/usr/bin/env python3
"""
Comprehensive GPU Environment Validation Script
Tests GPU detection, environment variables, PyTorch capabilities, and configuration
"""

import os
import sys
import platform
from pathlib import Path

# Load .env file if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from: {env_path}")
except ImportError:
    print("⚠ python-dotenv not installed, .env file won't be loaded automatically")
    print("  Install with: pip install python-dotenv")

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_mark(condition):
    """Return checkmark or X based on condition"""
    return "✓" if condition else "✗"

def test_environment_variables():
    """Test required environment variables"""
    print_header("Environment Variables Check")

    env_vars = {
        'OPENAI_API_KEY': 'Required for Whisper API transcription',
        'HF_TOKEN': 'Required for speaker diarization (pyannote)',
        'ANTHROPIC_API_KEY': 'Optional for Claude API',
        'VAST_CONTAINERLABEL': 'Vast.ai container identifier (if applicable)',
        'VAST_CONTAINER_USER': 'Vast.ai user identifier (if applicable)',
        'RUNPOD_POD_ID': 'RunPod pod identifier (if applicable)',
        'TRANSFORMERS_CACHE': 'Model cache directory (auto-set by gpu_config)',
        'HF_HOME': 'HuggingFace home directory (auto-set by gpu_config)',
    }

    results = {}
    for var, description in env_vars.items():
        value = os.environ.get(var)
        is_set = value is not None and len(value) > 0
        results[var] = is_set

        status = check_mark(is_set)
        if is_set:
            # Mask sensitive values
            if 'KEY' in var or 'TOKEN' in var:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value
            print(f"{status} {var:25s} = {display_value}")
        else:
            print(f"{status} {var:25s} (NOT SET) - {description}")

    return results

def test_pytorch_availability():
    """Test PyTorch installation and CUDA/MPS availability"""
    print_header("PyTorch Configuration")

    try:
        import torch
        print(f"✓ PyTorch installed: {torch.__version__}")
    except ImportError as e:
        print(f"✗ PyTorch NOT installed: {e}")
        return None

    results = {
        'torch_version': torch.__version__,
        'cuda_available': False,
        'mps_available': False,
        'cpu_only': True,
    }

    # Test CUDA
    print(f"\nCUDA Support:")
    cuda_available = torch.cuda.is_available()
    results['cuda_available'] = cuda_available
    print(f"{check_mark(cuda_available)} CUDA available: {cuda_available}")

    if cuda_available:
        results['cpu_only'] = False
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  Device count: {torch.cuda.device_count()}")

        for i in range(torch.cuda.device_count()):
            device_name = torch.cuda.get_device_name(i)
            props = torch.cuda.get_device_properties(i)
            vram_gb = props.total_memory / 1024**3
            print(f"  Device {i}: {device_name}")
            print(f"    VRAM: {vram_gb:.1f} GB")
            print(f"    Compute Capability: {props.major}.{props.minor}")
            results['device_name'] = device_name
            results['vram_gb'] = vram_gb
    else:
        print(f"  No NVIDIA GPU detected or CUDA not available")

    # Test MPS (Apple Silicon)
    print(f"\nMPS Support (Apple Silicon):")
    try:
        mps_available = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        results['mps_available'] = mps_available
        print(f"{check_mark(mps_available)} MPS available: {mps_available}")
        if mps_available:
            results['cpu_only'] = False
            print(f"  Apple Silicon GPU acceleration available")
    except Exception as e:
        print(f"  MPS check failed: {e}")

    # CPU fallback
    print(f"\nCPU Mode:")
    if results['cpu_only']:
        print(f"✓ Running in CPU-only mode (recommended: use pipeline.py)")
    else:
        print(f"  GPU acceleration available")

    return results

def test_gpu_config():
    """Test GPU configuration module"""
    print_header("GPU Configuration Module Test")

    try:
        # Import without running main
        import sys
        from pathlib import Path
        src_dir = Path(__file__).parent / 'src'
        sys.path.insert(0, str(src_dir))

        from gpu_config import detect_provider, GPUProvider

        provider = detect_provider()
        print(f"✓ GPU provider detection: {provider.value}")

        # Try to get optimal config (will fail gracefully on CPU-only systems)
        try:
            from gpu_config import get_optimal_config
            config = get_optimal_config()

            print(f"\nOptimal Configuration:")
            print(f"  Provider: {config.provider.value}")
            print(f"  Device: {config.device_name}")
            print(f"  VRAM: {config.vram_gb:.1f} GB")
            print(f"  Compute Type: {config.compute_type}")
            print(f"  Batch Size: {config.batch_size}")
            print(f"  TF32 Enabled: {config.enable_tf32}")
            print(f"  Num Workers: {config.num_workers}")
            print(f"  Model Cache: {config.model_cache_dir}")

            return {
                'provider': config.provider.value,
                'device_name': config.device_name,
                'vram_gb': config.vram_gb,
                'compute_type': config.compute_type,
                'batch_size': config.batch_size,
                'enable_tf32': config.enable_tf32,
                'model_cache_dir': config.model_cache_dir,
                'status': 'PASS'
            }

        except RuntimeError as e:
            print(f"\n⚠ GPU not available (expected on CPU-only systems):")
            print(f"  {str(e).split('GPU pipeline requires:')[0].strip()}")
            print(f"\n✓ CPU fallback detected correctly")
            return {
                'provider': provider.value,
                'status': 'CPU_ONLY',
                'message': 'No GPU available, use pipeline.py instead of pipeline_gpu.py'
            }

    except Exception as e:
        print(f"✗ GPU config module error: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'FAIL', 'error': str(e)}

def test_cache_directory():
    """Test model cache directory access"""
    print_header("Model Cache Directory Test")

    # Check if gpu_config has set cache directories
    transformers_cache = os.environ.get('TRANSFORMERS_CACHE')
    hf_home = os.environ.get('HF_HOME')

    # Default cache location
    default_cache = Path.home() / '.cache' / 'huggingface'

    cache_dir = Path(transformers_cache) if transformers_cache else default_cache

    print(f"Cache directory: {cache_dir}")
    print(f"Exists: {cache_dir.exists()}")

    # Test creation
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Cache directory created/verified: {cache_dir}")

        # Test write permissions
        test_file = cache_dir / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
            print(f"✓ Write permissions confirmed")
            return {
                'cache_dir': str(cache_dir),
                'exists': True,
                'writable': True,
                'status': 'PASS'
            }
        except Exception as e:
            print(f"✗ Write permission denied: {e}")
            return {
                'cache_dir': str(cache_dir),
                'exists': True,
                'writable': False,
                'status': 'FAIL',
                'error': str(e)
            }

    except Exception as e:
        print(f"✗ Cannot create cache directory: {e}")
        return {
            'cache_dir': str(cache_dir),
            'exists': False,
            'writable': False,
            'status': 'FAIL',
            'error': str(e)
        }

def test_system_info():
    """Print system information"""
    print_header("System Information")

    print(f"Platform: {platform.system()}")
    print(f"Platform Release: {platform.release()}")
    print(f"Platform Version: {platform.version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python Version: {sys.version}")
    print(f"Hostname: {platform.node()}")

def generate_final_report(env_results, pytorch_results, config_results, cache_results):
    """Generate final validation report"""
    print_header("FINAL VALIDATION REPORT")

    # Determine overall status
    critical_vars_present = (
        env_results.get('OPENAI_API_KEY', False) and
        env_results.get('HF_TOKEN', False)
    )

    pytorch_working = pytorch_results is not None
    cache_working = cache_results.get('status') == 'PASS'

    print("\nCritical Components:")
    print(f"{check_mark(critical_vars_present)} Required environment variables set")
    print(f"{check_mark(pytorch_working)} PyTorch installed and functional")
    print(f"{check_mark(cache_working)} Model cache directory accessible")

    # GPU Status
    print("\nGPU Status:")
    if pytorch_results and pytorch_results.get('cuda_available'):
        print(f"✓ GPU Available: {pytorch_results['device_name']}")
        print(f"  VRAM: {pytorch_results['vram_gb']:.1f} GB")
        print(f"  Recommended Pipeline: pipeline_gpu.py")
        overall_status = "PASS - GPU Acceleration Available"
    elif pytorch_results and pytorch_results.get('mps_available'):
        print(f"✓ Apple Silicon GPU (MPS) available")
        print(f"  Recommended Pipeline: pipeline.py (MPS not fully supported by all models)")
        overall_status = "PASS - MPS Available (Limited Support)"
    else:
        print(f"⚠ No GPU detected (CPU-only mode)")
        print(f"  Recommended Pipeline: pipeline.py (CPU/API-based)")
        overall_status = "PASS - CPU-Only Mode"

    # Configuration Status
    print("\nConfiguration:")
    if config_results:
        if config_results.get('status') == 'PASS':
            print(f"✓ GPU Configuration: Optimal settings generated")
            print(f"  Compute Type: {config_results['compute_type']}")
            print(f"  Batch Size: {config_results['batch_size']}")
        elif config_results.get('status') == 'CPU_ONLY':
            print(f"✓ CPU Configuration: Fallback mode detected")
        else:
            print(f"✗ Configuration Error: {config_results.get('error', 'Unknown')}")
            overall_status = "FAIL - Configuration Error"

    # Environment Variables Summary
    print("\nEnvironment Variables:")
    required_vars = ['OPENAI_API_KEY', 'HF_TOKEN']
    for var in required_vars:
        status = check_mark(env_results.get(var, False))
        print(f"{status} {var}")

    # Final Status
    print("\n" + "=" * 70)
    print(f"OVERALL STATUS: {overall_status}")
    print("=" * 70)

    # Deliverable metrics for orchestrator
    print("\n" + "=" * 70)
    print("DELIVERABLE METRICS (for orchestrator)")
    print("=" * 70)

    if pytorch_results and pytorch_results.get('cuda_available'):
        print(f"GPU detected: {pytorch_results['device_name']}, {pytorch_results['vram_gb']:.1f}GB VRAM")
        if config_results.get('status') == 'PASS':
            print(f"Optimal config: compute_type={config_results['compute_type']}, batch_size={config_results['batch_size']}, TF32={config_results['enable_tf32']}")
    else:
        print(f"GPU detected: No (CPU-only mode)")
        print(f"Optimal config: Use pipeline.py for CPU/API-based transcription")

    print(f"Environment variables: OPENAI_API_KEY={check_mark(env_results.get('OPENAI_API_KEY', False))}, HF_TOKEN={check_mark(env_results.get('HF_TOKEN', False))}")
    print(f"PyTorch CUDA: {'Available' if pytorch_results and pytorch_results.get('cuda_available') else 'Not Available'}")
    print(f"Cache directory: {cache_results['cache_dir']} (writable={cache_results.get('writable', False)})")
    print(f"Overall status: {overall_status}")

    return overall_status

if __name__ == "__main__":
    print("\n🔍 GPU Environment Validation Suite")
    print(f"Running from: {Path.cwd()}")

    # Run all tests
    test_system_info()
    env_results = test_environment_variables()
    pytorch_results = test_pytorch_availability()
    config_results = test_gpu_config()
    cache_results = test_cache_directory()

    # Generate final report
    final_status = generate_final_report(env_results, pytorch_results, config_results, cache_results)

    # Exit with appropriate code
    sys.exit(0 if "PASS" in final_status else 1)
