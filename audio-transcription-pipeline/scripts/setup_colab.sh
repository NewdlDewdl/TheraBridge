#!/bin/bash
# Colab L4 GPU Setup Script

echo "Setting up Colab L4 environment..."

# Install system dependencies
apt-get update -qq
apt-get install -y ffmpeg

# Install Python packages
pip install -q --upgrade pip
pip install -q -r requirements_colab.txt

# Download faster-whisper model
python -c "
from faster_whisper import WhisperModel
print('Downloading large-v3 model...')
model = WhisperModel('large-v3', device='cuda', compute_type='float16', download_root='/content/whisper_models')
print('Model downloaded successfully')
"

# Verify GPU
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"

echo "Setup complete!"