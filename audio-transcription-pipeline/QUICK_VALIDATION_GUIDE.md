# Quick GPU Validation Guide

## One-Command Validation

```bash
# Comprehensive validation (recommended)
python test_gpu_validation.py

# Detailed PyTorch analysis
python test_pytorch_detailed.py
```

## What Each Test Checks

### `test_gpu_validation.py` - Comprehensive Environment Check
- ✓ System information (OS, platform, hostname)
- ✓ Environment variables (OPENAI_API_KEY, HF_TOKEN, etc.)
- ✓ PyTorch installation and version
- ✓ CUDA availability and device properties
- ✓ MPS (Apple Silicon) support
- ✓ GPU provider detection (Vast.ai, RunPod, etc.)
- ✓ Optimal configuration generation
- ✓ Model cache directory access and permissions
- ✓ Final validation report with recommendations

### `test_pytorch_detailed.py` - Deep PyTorch Analysis
- ✓ PyTorch import and version
- ✓ CUDA detailed capabilities
- ✓ MPS detailed capabilities and tensor operations
- ✓ CPU operations (matrix multiplication, autograd)
- ✓ Backend preferences and priorities
- ✓ Whisper model compatibility (FFT, convolution, attention)
- ✓ Pipeline recommendations based on hardware

## Expected Output (Current System)

### On Apple Silicon Mac (Current Environment)
```
GPU Provider: unknown (local development)
GPU Available: No (NVIDIA), Yes (MPS - limited)
Environment Variables: ✓ All required keys set
PyTorch CUDA: Not Available (expected on macOS)
Cache Directory: ✓ Writable
Overall Status: PASS - CPU-Only Mode

Recommended Pipeline: pipeline.py (CPU/API-based)
```

### On NVIDIA GPU System (Vast.ai/RunPod)
```
GPU Provider: vast_ai (or runpod, lambda, etc.)
GPU Available: Yes (NVIDIA RTX 3090)
VRAM: 24.0 GB
Environment Variables: ✓ All required keys set
PyTorch CUDA: Available
Optimal Config: compute_type=int8, batch_size=8, TF32=False
Cache Directory: ✓ Writable
Overall Status: PASS - GPU Acceleration Available

Recommended Pipeline: pipeline_gpu.py (GPU-accelerated)
```

## Quick Troubleshooting

### Environment Variables Not Set
```bash
# Check if .env file exists
ls -la .env

# Load manually if needed
source .env  # bash/zsh
set -a; source .env; set +a  # more reliable

# Or create .env from example
cp .env.example .env
# Edit .env with your API keys
```

### PyTorch Not Installed
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install PyTorch separately
pip install torch torchvision torchaudio
```

### CUDA Not Available (on GPU system)
```bash
# Check NVIDIA driver
nvidia-smi

# Check PyTorch CUDA build
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Version: {torch.version.cuda}')"

# Reinstall PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Cache Directory Not Writable
```bash
# Check permissions
ls -ld ~/.cache/huggingface

# Create if missing
mkdir -p ~/.cache/huggingface

# Fix permissions
chmod -R u+w ~/.cache/huggingface
```

## Files Generated

| File | Purpose | Size |
|------|---------|------|
| `test_gpu_validation.py` | Comprehensive validation script | ~13KB |
| `test_pytorch_detailed.py` | Detailed PyTorch analysis | ~8KB |
| `GPU_VALIDATION_REPORT.md` | Full validation report | ~9KB |
| `QUICK_VALIDATION_GUIDE.md` | This guide | ~3KB |

## For Orchestrator Review

**Instance I1 Deliverables:**
- ✅ 2 comprehensive test scripts created
- ✅ All validation criteria met (5/5 pass)
- ✅ Detailed markdown report generated
- ✅ Quick reference guide created
- ✅ Environment validated for CPU/API pipeline
- ✅ Recommendations documented

**Status:** Ready for pipeline integration testing (Instance I2, I3, I4)
