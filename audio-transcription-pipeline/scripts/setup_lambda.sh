#!/bin/bash
# Lambda Labs Instance Setup Script
set -e

echo "Lambda Labs GPU Setup"
echo "====================="

# Lambda typically has ML frameworks pre-installed
# Verify PyTorch CUDA support
python3 << INNEREOF
import torch
assert torch.cuda.is_available(), "CUDA not available"
print(f"PyTorch {torch.__version__}")
print(f"CUDA {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
INNEREOF

# Create virtual environment (recommended on Lambda)
python3 -m venv ~/transcribe-env
source ~/transcribe-env/bin/activate

# Install packages
pip install --upgrade pip
pip install faster-whisper==1.0.0
pip install pyannote.audio==3.1.1
pip install python-dotenv
pip install julius

# Setup directories
mkdir -p ~/models ~/logs ~/outputs

echo ""
echo "Lambda Labs setup complete!"
echo "Activate environment: source ~/transcribe-env/bin/activate"
