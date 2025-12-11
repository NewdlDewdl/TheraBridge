#!/bin/bash
# Vast.ai Instance Setup Script
set -e

echo "Vast.ai GPU Setup"
echo "================="

# Install system dependencies (if needed)
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    apt-get update && apt-get install -y ffmpeg git
fi

# Clone repository (if running on fresh instance)
if [ ! -d "audio-transcription-pipeline" ]; then
    echo "Cloning repository..."
    git clone https://github.com/yourusername/audio-transcription-pipeline.git
    cd audio-transcription-pipeline
fi

# Run universal setup
bash scripts/setup_gpu.sh

echo ""
echo "Vast.ai setup complete!"
echo "This instance is optimized for Vast.ai infrastructure."
