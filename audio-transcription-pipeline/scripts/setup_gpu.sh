#!/bin/bash
set -e

echo "=========================================="
echo "GPU Transcription Pipeline Setup"
echo "=========================================="

# Detect Python version
PYTHON_CMD=$(command -v python3.10 || command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python: $PYTHON_CMD (version $PYTHON_VERSION)"

# Detect GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found. GPU setup requires NVIDIA GPU."
    exit 1
fi

echo ""
echo "GPU Information:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Detect CUDA version
CUDA_VERSION=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9.]+' | head -1)
echo ""
echo "Detected CUDA version: $CUDA_VERSION"

# Install PyTorch with matching CUDA version
if [[ "$CUDA_VERSION" == 12.* ]]; then
    echo "Installing PyTorch for CUDA 12.x..."
    pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
elif [[ "$CUDA_VERSION" == 11.* ]]; then
    echo "Installing PyTorch for CUDA 11.x..."
    pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
else
    echo "WARNING: Unsupported CUDA version. Installing default PyTorch..."
    pip install torch torchvision torchaudio
fi

# Install transcription packages
echo ""
echo "Installing transcription packages..."
pip install faster-whisper==1.0.0
pip install pyannote.audio==3.1.1
pip install python-dotenv
pip install psutil gputil
pip install julius

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA version: {torch.version.cuda}')" || true
python -c "from faster_whisper import WhisperModel; print('faster-whisper: OK')"
python -c "from pyannote.audio import Pipeline; print('pyannote.audio: OK')"

# Create directories
mkdir -p models logs outputs

# Setup environment file
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << EOF
# HuggingFace Token (required for pyannote diarization)
# Get token at: https://huggingface.co/settings/tokens
# Accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
HF_TOKEN=your_token_here

# Model cache directory (auto-detected, override if needed)
# TRANSFORMERS_CACHE=./models
# HF_HOME=./models
EOF
    echo "Created .env file. Please edit and add your HF_TOKEN."
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your HuggingFace token"
echo "2. Activate environment: source venv/bin/activate"
echo "3. Test GPU: python src/gpu_config.py"
echo "4. Run pipeline: python src/pipeline_gpu.py <audio_file>"
echo ""
