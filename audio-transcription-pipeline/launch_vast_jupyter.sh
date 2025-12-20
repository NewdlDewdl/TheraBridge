#!/bin/bash
#
# Launch Vast.ai GPU instance with Jupyter notebook
# Simple, clean setup from scratch
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Vast.ai GPU + Jupyter Launcher${NC}"
echo -e "${BLUE}================================${NC}\n"

# Step 1: Search for GPU instances
echo -e "${YELLOW}Step 1: Searching for available GPUs...${NC}\n"

vastai search offers 'gpu_name=RTX_4090 reliability>0.98 disk_space>=50' \
    --order 'dph+' | head -10

echo -e "\n${GREEN}Showing top 10 cheapest RTX 4090 instances${NC}"
echo -e "${YELLOW}Note the OFFER_ID of the instance you want to rent${NC}\n"

read -p "Enter OFFER_ID to rent (or press Enter to exit): " OFFER_ID

if [ -z "$OFFER_ID" ]; then
    echo "Exiting..."
    exit 0
fi

# Step 2: Create instance with Jupyter
echo -e "\n${YELLOW}Step 2: Creating GPU instance with Jupyter...${NC}\n"

INSTANCE_ID=$(vastai create instance $OFFER_ID \
    --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime \
    --disk 50 \
    --jupyter \
    --jupyter-dir / \
    --jupyter-lab \
    --direct-port-count 1 \
    --label "therapy-pipeline-jupyter" \
    | grep -oE "[0-9]+")

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}Failed to create instance${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Instance created: $INSTANCE_ID${NC}"

# Step 3: Wait for instance to start
echo -e "\n${YELLOW}Step 3: Waiting for instance to start...${NC}"

for i in {1..30}; do
    STATUS=$(vastai show instances | grep "^$INSTANCE_ID" | awk '{print $3}')

    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✓ Instance is running${NC}"
        break
    fi

    echo -n "."
    sleep 2
done

# Step 4: Get connection details
echo -e "\n${YELLOW}Step 4: Getting connection details...${NC}\n"

vastai show instances | grep "^$INSTANCE_ID"

# Extract SSH and Jupyter details
SSH_HOST=$(vastai show instances | grep "^$INSTANCE_ID" | awk '{print $10}')
SSH_PORT=$(vastai show instances | grep "^$INSTANCE_ID" | awk '{print $11}')

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}INSTANCE READY!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "${BLUE}Instance ID:${NC} $INSTANCE_ID"
echo -e "${BLUE}SSH:${NC} ssh -p $SSH_PORT root@$SSH_HOST"
echo ""
echo -e "${YELLOW}Jupyter will be available shortly at:${NC}"
echo -e "  Check 'vastai show instances' for the Jupyter URL"
echo ""

# Step 5: Setup instructions
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}NEXT STEPS${NC}"
echo -e "${BLUE}================================${NC}\n"

cat << 'EOF'
1. Wait ~1 minute for Jupyter to start
2. Run: vastai show instances
3. Look for the "Jupyter" column - it will show a URL like:
   https://jupyter-12345.vast.ai:xxxxx/?token=...
4. Open that URL in your browser
5. Upload the notebook and audio file:
   - Upload: gpu_pipeline_notebook.ipynb
   - Upload: your audio file (rename to test_audio.mp3)
6. Run the notebook cells to process audio!

To upload files via command line:
  scp -P <SSH_PORT> gpu_pipeline_notebook.ipynb root@<SSH_HOST>:~/
  scp -P <SSH_PORT> your_audio.mp3 root@<SSH_HOST>:~/test_audio.mp3

IMPORTANT: When done, destroy the instance:
  vastai destroy instance <INSTANCE_ID>
EOF

echo -e "\n${GREEN}✓ Setup complete!${NC}\n"
