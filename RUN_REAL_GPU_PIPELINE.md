# Run Real Audio Processing on Vast.ai GPU

This guide will walk you through processing a real 1-hour therapy session audio file using Vast.ai GPU instances.

## Prerequisites

✅ Vast.ai CLI installed (`vastai` command)
✅ Audio files available in `audio-transcription-pipeline/tests/samples/`
✅ HuggingFace token for pyannote diarization
✅ OpenAI API key (optional, for API fallback)

## Step 1: Authenticate with Vast.ai

First, you need to get your API key from Vast.ai:

1. Go to https://cloud.vast.ai/
2. Sign in or create an account
3. Add credits ($10-20 recommended for testing)
4. Go to Account → API Key
5. Copy your API key

Then authenticate:

```bash
vastai set api-key YOUR_API_KEY_HERE
```

## Step 2: Find Available GPU Instances

Search for affordable L4 GPU instances (recommended for this workload):

```bash
# Search for L4 GPUs with at least 24GB VRAM, sorted by price
vastai search offers 'gpu_name=L4 disk_space>=50 inet_down>=100' --order 'dph+'

# Example output:
#  ID     $/hr   GPU                VRAM    Disk   Download   Location
#  12345  0.30   1x RTX_4090_L4     24 GB   100GB  500 Mbps   EU-Netherlands
#  23456  0.32   1x RTX_4090_L4     24 GB   150GB  1000 Mbps  US-California
```

**Cost estimate:** L4 instances cost ~$0.25-0.50/hour. Processing 1-hour audio takes ~5-10 minutes, so total cost: **~$0.05-0.10 per run**.

## Step 3: Create (Rent) a GPU Instance

Rent an instance (replace OFFER_ID with the ID from search results):

```bash
# Create instance with PyTorch image
vastai create instance OFFER_ID \
  --image pytorch/pytorch:2.6.0-cuda12.1-cudnn9-devel \
  --disk 50 \
  --label therapy-pipeline

# Wait for instance to start (check status)
vastai show instances

# Example output:
#  ID     STATUS    $/hr   GPU          SSH_HOST           SSH_PORT
#  78910  running   0.30   1x L4        ssh4.vast.ai       12345
```

**Note the instance ID and SSH connection details!**

## Step 4: Connect to Your Instance

Use SSH to connect (replace with your instance details):

```bash
# Connect via SSH (get details from 'vastai show instances')
ssh -p SSH_PORT root@SSH_HOST

# Example:
ssh -p 12345 root@ssh4.vast.ai
```

## Step 5: Setup Pipeline on GPU Instance

Once connected to your Vast.ai instance:

```bash
# Clone your repository (or upload files)
git clone https://github.com/evolvedtroglodyte/TheraBridge.git
cd TheraBridge/audio-transcription-pipeline

# Run GPU setup script
bash scripts/setup_gpu.sh

# Configure environment
source venv/bin/activate

# Add your HuggingFace token (required for pyannote diarization)
echo "HF_TOKEN=your_huggingface_token_here" >> .env

# Verify GPU is detected
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0)}')"
```

## Step 6: Upload Audio File

From your local machine, upload the audio file to Vast.ai:

```bash
# Find your largest audio file (1-hour session)
ls -lh audio-transcription-pipeline/tests/samples/*.mp3

# Upload to Vast.ai instance (replace SSH details)
scp -P SSH_PORT \
  "audio-transcription-pipeline/tests/samples/Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3" \
  root@SSH_HOST:~/TheraBridge/audio-transcription-pipeline/test_audio.mp3

# Example:
scp -P 12345 \
  "audio-transcription-pipeline/tests/samples/Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3" \
  root@ssh4.vast.ai:~/TheraBridge/audio-transcription-pipeline/test_audio.mp3
```

## Step 7: Run the Real GPU Pipeline

Back on the Vast.ai instance (via SSH):

```bash
# Activate environment
cd ~/TheraBridge/audio-transcription-pipeline
source venv/bin/activate

# Check audio duration
python -c "from pydub import AudioSegment; audio = AudioSegment.from_file('test_audio.mp3'); print(f'Duration: {len(audio)/1000/60:.1f} minutes')"

# Run GPU pipeline with timing
time python -c "
from src.pipeline_gpu import GPUTranscriptionPipeline
import json
from pathlib import Path

# Process audio
with GPUTranscriptionPipeline(whisper_model='large-v3') as pipeline:
    result = pipeline.process(
        audio_path='test_audio.mp3',
        num_speakers=2,
        language='en',
        enable_diarization=True
    )

# Save results
output_file = 'gpu_results.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f'\nResults saved to {output_file}')
print(f'Total processing time: {result[\"performance\"][\"total_time_seconds\"]:.2f} seconds')
print(f'Transcript segments: {len(result[\"transcript\"])}')
print(f'Speaker turns: {len(result.get(\"diarization\", []))}')
"
```

## Step 8: Download Results

From your local machine:

```bash
# Download results
scp -P SSH_PORT root@SSH_HOST:~/TheraBridge/audio-transcription-pipeline/gpu_results.json ./gpu_results_real.json

# Download performance logs
scp -r -P SSH_PORT root@SSH_HOST:~/TheraBridge/audio-transcription-pipeline/tests/outputs/performance_logs ./vast_performance_logs/

# View results
cat gpu_results_real.json | jq '.performance'
```

## Step 9: DESTROY INSTANCE (Stop Billing!)

**CRITICAL:** Vast.ai charges per second. Always destroy your instance when done:

```bash
# From your local machine
vastai destroy instance INSTANCE_ID

# Verify it's destroyed
vastai show instances
```

## Alternative: Using Backend Integration

Instead of running the pipeline directly, you can integrate with the backend's new parallel processing service:

```python
# On Vast.ai instance
from backend.app.services.gpu_pipeline_wrapper import VastAIGPUService
from backend.app.database import get_db
from uuid import UUID

# Initialize service
gpu_service = VastAIGPUService(
    db=next(get_db()),
    progress_tracker=None  # Optional
)

# Process via backend service
result = await gpu_service.process_audio_gpu(
    session_id=UUID('your-session-id'),
    audio_path='test_audio.mp3',
    num_speakers=2
)

print(f"Processing time: {result['performance']['total_time_seconds']}s")
```

## Expected Performance

Based on L4 GPU benchmarks:

| Audio Duration | Expected Processing Time | Cost (@ $0.30/hr) |
|----------------|-------------------------|-------------------|
| 1 minute       | ~10-15 seconds          | ~$0.001           |
| 5 minutes      | ~30-45 seconds          | ~$0.004           |
| 10 minutes     | ~1-2 minutes            | ~$0.01            |
| 30 minutes     | ~3-5 minutes            | ~$0.025           |
| **1 hour**     | **~5-10 minutes**       | **~$0.05**        |

**Key factors affecting speed:**
- Transcription: ~0.1-0.15x real-time (1hr audio = 6-9min)
- Diarization: ~0.05-0.1x real-time (1hr audio = 3-6min)
- Parallel execution reduces total to ~5-10 minutes

## Troubleshooting

### GPU Out of Memory
```bash
# Use smaller model
python ... --whisper_model medium  # Instead of large-v3
```

### Diarization Fails
```bash
# Check HF token is set
cat .env | grep HF_TOKEN

# Accept pyannote license at https://huggingface.co/pyannote/speaker-diarization-3.1
```

### Slow Download/Upload
```bash
# Use instances with >500 Mbps bandwidth
vastai search offers 'inet_down>=500' --order 'dph+'
```

## Cost Optimization Tips

1. **Use spot instances:** Search with `--order 'dph+'` for cheapest options
2. **Batch processing:** Upload multiple files, process them all, then destroy
3. **Use smaller models:** `medium` instead of `large-v3` for 50% cost reduction
4. **Monitor usage:** Set up billing alerts in Vast.ai dashboard
5. **Always destroy:** Never leave instances running when not in use

## Next Steps

After getting real results:

1. **Update performance benchmarks** in `backend/tests/outputs/performance_report.json`
2. **Compare CPU vs GPU** processing times
3. **Document real-world costs** for production planning
4. **Test with longer audio** (2+ hours) to verify chunking works
5. **Integrate with backend** for automatic GPU processing

---

**Questions or issues?** Check the full pipeline documentation in `audio-transcription-pipeline/README.md`
