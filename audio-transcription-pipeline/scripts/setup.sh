#!/bin/bash

# Audio Transcription Pipeline Setup Script
# =========================================

set -e

echo "=================================="
echo "Audio Transcription Pipeline Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if ffmpeg is installed (required for audio processing)
echo -e "${BLUE}Checking ffmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓ ffmpeg is installed${NC}"
else
    echo -e "${YELLOW}⚠ ffmpeg not found${NC}"
    echo "ffmpeg is required for audio processing."
    echo ""
    echo "Install ffmpeg:"
    echo "  macOS:  brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
    echo "  CentOS: sudo yum install ffmpeg"
    echo ""
    read -p "Continue without ffmpeg? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo -e "${BLUE}Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip -q
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install requirements
echo ""
echo -e "${BLUE}Installing Python packages...${NC}"
echo "This may take a few minutes..."

# Install core requirements first
pip install -q pydub numpy scipy

# Install Whisper (choose one)
echo ""
echo -e "${BLUE}Select Whisper implementation:${NC}"
echo "  1) OpenAI Whisper (original, more features)"
echo "  2) Faster Whisper (optimized for CPU)"
echo "  3) Both"
echo "  4) Skip (use API instead)"
read -p "Choice (1-4): " whisper_choice

case $whisper_choice in
    1)
        echo "Installing OpenAI Whisper..."
        pip install -q openai-whisper
        ;;
    2)
        echo "Installing Faster Whisper..."
        pip install -q faster-whisper
        ;;
    3)
        echo "Installing both Whisper implementations..."
        pip install -q openai-whisper faster-whisper
        ;;
    4)
        echo "Skipping local Whisper installation"
        ;;
    *)
        echo "Invalid choice, skipping Whisper"
        ;;
esac

# Install remaining packages
echo ""
echo -e "${BLUE}Installing remaining packages...${NC}"
pip install -q python-dotenv pydantic tqdm colorama

echo ""
echo -e "${GREEN}✓ Core packages installed${NC}"

# Create directory structure
echo ""
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p inputs
mkdir -p outputs
mkdir -p models
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << 'EOF'
# OpenAI API Key (for Whisper API)
OPENAI_API_KEY=

# Anthropic API Key (for Claude post-processing)
ANTHROPIC_API_KEY=

# Audio Processing Settings
MAX_AUDIO_LENGTH_MINUTES=60
DEFAULT_WHISPER_MODEL=base
ENABLE_DIARIZATION=true

# Output Settings
DEFAULT_OUTPUT_FORMAT=conversation
SAVE_INTERMEDIATE_FILES=false

# Performance Settings
USE_GPU=false
BATCH_SIZE=1
NUM_WORKERS=1
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo ""
    echo -e "${YELLOW}Don't forget to add your API keys to the .env file!${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Test the pipeline
echo ""
echo -e "${BLUE}Testing pipeline setup...${NC}"
python3 -c "
import sys
try:
    import pydub
    import numpy
    print('✓ Core imports successful')
except ImportError as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pipeline setup successful!${NC}"
else
    echo -e "${RED}✗ Pipeline setup failed${NC}"
    exit 1
fi

# Download a small Whisper model if requested
echo ""
read -p "Download small Whisper model for testing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Downloading Whisper base model...${NC}"
    python3 -c "
try:
    import whisper
    model = whisper.load_model('base')
    print('✓ Whisper base model downloaded')
except:
    print('Whisper not installed or download failed')
    "
fi

echo ""
echo "=================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================="
echo ""
echo "To run the pipeline:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the pipeline:"
echo "     python pipeline.py"
echo ""
echo "  3. Or use the test script:"
echo "     ./test-whisper-api.sh"
echo ""
echo "Directory structure:"
echo "  inputs/  - Place audio files here"
echo "  outputs/ - Transcriptions will be saved here"
echo "  models/  - Downloaded models"
echo "  logs/    - Processing logs"
echo ""