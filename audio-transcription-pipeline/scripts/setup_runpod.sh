#!/bin/bash
# RunPod Instance Setup Script
set -e

echo "RunPod GPU Setup"
echo "================"

# RunPod typically has PyTorch pre-installed
# Check and upgrade if needed
if python3 -c "import torch" 2>/dev/null; then
    echo "PyTorch already installed"
    python3 -c "import torch; print(f'Version: {torch.__version__}')"
else
    echo "PyTorch not found, installing..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

# Install transcription-specific packages
pip install faster-whisper==1.0.0
pip install pyannote.audio==3.1.1
pip install python-dotenv psutil gputil
pip install julius

# Create directories
mkdir -p /workspace/models /workspace/logs /workspace/outputs

# Setup environment
cat > /workspace/.env << INNEREOF
HF_TOKEN=${HF_TOKEN:-your_token_here}
TRANSFORMERS_CACHE=/workspace/models
HF_HOME=/workspace/models
INNEREOF

echo ""
echo "RunPod setup complete!"
echo "Models will be cached in /workspace/models"
