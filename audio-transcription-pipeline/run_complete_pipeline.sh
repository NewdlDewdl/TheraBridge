#!/bin/bash
# Complete pipeline test script
# Runs the entire transcription pipeline from audio to professional HTML output

echo "============================================================"
echo "COMPLETE TRANSCRIPTION PIPELINE TEST"
echo "============================================================"
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create it first with: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📌 Activating virtual environment...${NC}"
source venv/bin/activate

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env with OPENAI_API_KEY and HF_TOKEN"
    exit 1
fi

# Step 1: Check if we have existing diarization output
if [ -f "tests/outputs/diarization_output.json" ]; then
    echo -e "${GREEN}✅ Found existing diarization output${NC}"
    echo "Skipping transcription and diarization steps..."
    echo

    # Step 2: Apply improved alignment
    echo -e "${YELLOW}📌 Step 1: Applying improved alignment algorithm...${NC}"
    python3 apply_improved_alignment.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Alignment failed${NC}"
        exit 1
    fi
    echo

else
    echo -e "${YELLOW}⚠️  No existing diarization output found${NC}"
    echo "Would need to run full pipeline (requires API calls)"
    echo

    # Uncomment these lines to run full pipeline with API calls:
    # echo -e "${YELLOW}📌 Running full transcription pipeline...${NC}"
    # python3 tests/test_full_pipeline_improved.py
    # if [ $? -ne 0 ]; then
    #     echo -e "${RED}❌ Pipeline failed${NC}"
    #     exit 1
    # fi
fi

# Step 3: Generate professional HTML output
echo -e "${YELLOW}📌 Step 2: Generating professional HTML output...${NC}"
python3 tests/test_formatted_output_professional.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ HTML generation failed${NC}"
    exit 1
fi
echo

# Step 4: Show results
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ PIPELINE COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo

echo "Generated files:"
echo "  - tests/outputs/diarization_output_improved.json"
echo "  - tests/outputs/transcription_professional.html"
echo

# Try to open HTML in browser (works on macOS)
if command -v open &> /dev/null; then
    echo -e "${YELLOW}Opening HTML in browser...${NC}"
    open tests/outputs/transcription_professional.html
else
    echo "To view the results, open:"
    echo "  tests/outputs/transcription_professional.html"
fi

echo
echo "HTML Color Scheme:"
echo "  • Therapist: Teal (#1abc9c) - Professional, calming"
echo "  • Client: Orange (#e67e22) - Warm, engaging"
echo "  • Unknown: Gray (#95a5a6) - Neutral"
echo "  • No gradients - Clean, professional solid colors"
echo