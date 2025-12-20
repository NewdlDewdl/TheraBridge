# Simple GPU Pipeline Setup - From Scratch

Everything has been reset. Here's how to run the GPU pipeline in Jupyter notebook from scratch.

## ✅ What's Been Cleaned Up

- ✓ Destroyed all running Vast.ai instances (saved you from ongoing billing)
- ✓ Killed all background processes
- ✓ Cleaned output directories
- ✓ Fresh start guaranteed

## 🚀 Quick Start (3 Steps)

### Step 1: Launch Vast.ai Instance with Jupyter

```bash
cd audio-transcription-pipeline
./launch_vast_jupyter.sh
```

This will:
- Search for cheap GPU instances (RTX 4090 recommended)
- Ask you to select an OFFER_ID
- Create instance with Jupyter Lab pre-installed
- Show you the Jupyter URL

### Step 2: Upload Files to Instance

Once instance is running, upload the notebook and audio:

```bash
# Get SSH details from: vastai show instances
# Look for SSH_HOST and SSH_PORT

# Upload notebook
scp -P <SSH_PORT> gpu_pipeline_notebook.ipynb root@<SSH_HOST>:~/

# Upload audio file (the 46-minute Carl Rogers session)
scp -P <SSH_PORT> "tests/samples/Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3" root@<SSH_HOST>:~/test_audio.mp3
```

### Step 3: Open Jupyter & Run

1. Get Jupyter URL: `vastai show instances` (look for https://jupyter-xxxxx.vast.ai link)
2. Open URL in browser
3. Open `gpu_pipeline_notebook.ipynb`
4. Run cells one by one to see real-time results

## 📓 What the Notebook Does

The notebook has cells for:

1. **Setup** - Check GPU availability, VRAM
2. **Import Pipeline** - Load the GPU transcription code
3. **Configuration** - Set audio file, number of speakers
4. **Check Audio** - Show duration, estimate processing time
5. **Initialize** - Create the GPU pipeline
6. **Process** - Run the actual transcription + diarization
7. **Show Metrics** - Display processing time, GPU utilization, speedup
8. **Show Transcript** - Display diarized transcript with speaker labels
9. **Save Results** - Export to JSON file
10. **Cleanup** - Release GPU memory

## 📊 Expected Results (46-minute audio)

- **Processing time:** ~5-8 minutes
- **Speedup:** ~6-9x real-time
- **Cost:** ~$0.05-0.10 (RTX 4090 @ $0.40/hr)
- **Output:** Complete transcript with speaker labels + performance metrics

## 🔧 Alternative: Manual Setup (If Script Fails)

If the launcher script has issues, here's the manual process:

```bash
# 1. Search for GPUs
vastai search offers 'gpu_name=RTX_4090 reliability>0.98' --order 'dph+'

# 2. Create instance with Jupyter
vastai create instance <OFFER_ID> \
  --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime \
  --disk 50 \
  --jupyter \
  --jupyter-lab \
  --label therapy-pipeline

# 3. Wait for instance to start
vastai show instances

# 4. Get Jupyter URL from the output
# 5. Upload files via SSH
# 6. Open Jupyter and run notebook
```

## ⚠️ Important: Destroy Instance When Done

```bash
# Get instance ID
vastai show instances

# Destroy it
vastai destroy instance <INSTANCE_ID>
```

**Vast.ai bills per second** - always destroy when finished!

## 🆘 Troubleshooting

**Problem: Can't find Jupyter URL**
- Wait 1-2 minutes after instance starts
- Run: `vastai show instances` - look for URL in output
- Sometimes it takes a minute for Jupyter to initialize

**Problem: Notebook can't import pipeline**
- SSH into instance: `ssh -p <PORT> root@<HOST>`
- Clone repo: `git clone https://github.com/evolvedtroglodyte/TheraBridge.git`
- Install deps: `cd TheraBridge/audio-transcription-pipeline && bash scripts/setup_gpu.sh`
- Upload notebook to that directory

**Problem: Out of GPU memory**
- Use smaller model: Change `WHISPER_MODEL = "medium"` instead of "large-v3"
- Rent instance with more VRAM (24GB+ recommended)

**Problem: HuggingFace token error**
- Get token from: https://huggingface.co/settings/tokens
- Accept license: https://huggingface.co/pyannote/speaker-diarization-3.1
- In notebook, add cell: `os.environ['HF_TOKEN'] = 'your_token_here'`

## 📁 Files Created

- `gpu_pipeline_notebook.ipynb` - Interactive Jupyter notebook
- `launch_vast_jupyter.sh` - Automated Vast.ai launcher
- `SIMPLE_GPU_GUIDE.md` - This file

## 🎯 Goal

Run the GPU pipeline interactively in Jupyter and see:
- Real processing time for 46-minute audio
- GPU utilization metrics
- Diarized transcript with speaker labels
- Cost breakdown

No more complex scripts - just upload, run cells, see results!
