#!/bin/bash
# Paperspace Gradient Setup Script
set -e

echo "Paperspace Gradient GPU Setup"
echo "=============================="

# Paperspace uses /storage for persistent data
STORAGE_DIR="/storage/transcription"
mkdir -p $STORAGE_DIR/models $STORAGE_DIR/logs $STORAGE_DIR/outputs

# Install packages
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install faster-whisper==1.0.0
pip install pyannote.audio==3.1.1
pip install python-dotenv psutil gputil
pip install julius

# Setup environment
cat > $STORAGE_DIR/.env << INNEREOF
HF_TOKEN=${HF_TOKEN:-your_token_here}
TRANSFORMERS_CACHE=/storage/transcription/models
HF_HOME=/storage/transcription/models
INNEREOF

# Create symlink to storage
ln -sf $STORAGE_DIR ~/transcription

echo ""
echo "Paperspace setup complete!"
echo "Models cached in: /storage/transcription/models"
echo "Edit .env in: /storage/transcription/.env"
