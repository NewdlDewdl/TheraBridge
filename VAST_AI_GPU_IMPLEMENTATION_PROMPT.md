# Vast.ai GPU Pipeline Implementation Prompt

Use this prompt with the orchestrator to implement GPU pipeline testing on Vast.ai:

---

## Orchestrator Prompt

```
/cl:orchestrate Implement and test the GPU audio transcription pipeline on Vast.ai. The Vast.ai CLI is already installed and configured. Focus ONLY on:

1. **Launch Vast.ai Instance**:
   - Use existing Vast.ai CLI commands
   - Launch RTX 3090 instance (24GB VRAM, recommended in docs)
   - Use image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
   - Mount storage: /workspace for persistent model cache
   - Open ports: 22 (SSH), 8080 (Jupyter if needed)
   - Budget: $0.20/hour target

2. **Setup GPU Environment**:
   - SSH into the launched instance
   - Run existing setup script: bash scripts/setup_gpu.sh
   - This script installs requirements_gpu.txt (faster-whisper, pyannote.audio, torch, torchaudio)
   - Verify GPU detection: python test_gpu_validation.py
   - Confirm CUDA available, provider detected as VASTAI
   - Verify model cache at /workspace/models

3. **Test GPU Pipeline with Same 3 Audio Files**:
   - File 1: Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3 (35 min)
   - File 2: LIVE Cognitive Behavioral Therapy Session (1).mp3 (23 min)
   - File 3: Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3 (46 min)
   - Use pipeline_gpu.py (NOT pipeline.py)
   - Measure: processing time, GPU utilization, VRAM usage, speed ratio
   - Expected: 30-50x real-time (vs 4.28x CPU achieved)
   - Verify model caching: 2nd run should be 18% faster

4. **GPU Utilization Validation**:
   - Monitor GPU usage during transcription stage (should be 80-95%)
   - Monitor GPU usage during diarization stage (should be 70-90%)
   - Check VRAM usage (should peak at 8-12GB for large-v3 model)
   - Verify TF32 disabled (RTX 3090 uses int8 compute_type per gpu_config.py)
   - Confirm batch_size=8 being used

5. **Compare GPU vs CPU Results**:
   - Processing time: GPU vs CPU (should be 10-15x faster)
   - Cost per file: GPU instance cost vs CPU API cost
   - Quality: Alignment % should be identical
   - Speed ratio: GPU 30-50x vs CPU 4.28x
   - Break-even analysis: At what volume does GPU become cheaper?

6. **Generate GPU Test Report**:
   - JSON: tests/outputs/gpu_pipeline_results_YYYYMMDD.json
   - Markdown: tests/outputs/GPU_PIPELINE_VALIDATION_REPORT.md
   - Include: performance metrics, GPU utilization, cost analysis, CPU comparison
   - Recommendation: When to use GPU vs CPU in production

7. **Cleanup and Cost Management**:
   - Destroy Vast.ai instance after testing (CRITICAL to stop billing)
   - Calculate total cost: (processing time + setup time) × $0.20/hr
   - Expected total: ~$0.50-1.00 for full validation
   - Document instance destruction command for safety

IMPORTANT CONSTRAINTS:
- Do NOT modify pipeline_gpu.py, gpu_config.py, or gpu_audio_ops.py (already implemented)
- Do NOT create new GPU scripts (use existing scripts/)
- Do NOT install additional dependencies (requirements_gpu.txt is complete)
- Do NOT test on local machine (no NVIDIA GPU available)
- Do FOCUS on Vast.ai deployment, testing, and validation ONLY

SUCCESS CRITERIA:
- Vast.ai instance launched successfully
- GPU detected and configured (RTX 3090, VASTAI provider)
- All 3 audio files processed with GPU pipeline
- Performance metrics captured (speed, GPU util, VRAM, cost)
- GPU vs CPU comparison complete
- Total cost ≤ $1.00
- Instance destroyed to stop billing
- Comprehensive GPU validation report generated
```

---

## Background Context

**What's Already Done:**
- ✅ GPU pipeline fully implemented (pipeline_gpu.py, gpu_config.py, gpu_audio_ops.py)
- ✅ Vast.ai CLI installed and configured
- ✅ Setup scripts ready (scripts/setup_gpu.sh, scripts/setup_vast_api.sh)
- ✅ Test validation scripts ready (test_gpu_validation.py, test_pytorch_detailed.py)
- ✅ CPU baseline established (4.28x real-time, 85% alignment, 3 files tested)
- ✅ GPU documentation complete (setup guide, cost analysis, provider detection logic)

**What Needs to Be Done:**
- Launch Vast.ai RTX 3090 instance
- Setup GPU environment on instance
- Run GPU pipeline tests on same 3 audio files
- Validate GPU performance vs CPU baseline
- Generate comparison report
- Destroy instance (stop billing)

**Expected Outcomes:**
- GPU processing speed: 30-50x real-time (vs 4.28x CPU)
- GPU cost per file: $0.002 (vs $0.018 CPU)
- Total validation cost: ~$0.50-1.00
- Quality identical to CPU (85% alignment)
- Break-even point: 20-30 sessions/day

---

## Quick Reference

**Vast.ai CLI Commands:**
```bash
# Search for RTX 3090 instances
vastai search offers 'gpu_name=RTX_3090 gpu_ram>=24 reliability>0.98'

# Launch instance (example)
vastai create instance <INSTANCE_ID> \
  --image pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime \
  --disk 50 \
  --ssh

# Check instance status
vastai show instances

# SSH into instance
ssh -p <PORT> root@<HOST>

# Destroy instance (IMPORTANT)
vastai destroy instance <INSTANCE_ID>
```

**GPU Pipeline Commands (on Vast.ai instance):**
```bash
# Clone repo
git clone <repo_url>
cd audio-transcription-pipeline

# Setup environment
bash scripts/setup_gpu.sh

# Validate GPU
python test_gpu_validation.py

# Run GPU pipeline test
python test_gpu_pipeline.py  # Or use existing test scripts
```

**Cost Calculation:**
- RTX 3090 on Vast.ai: ~$0.20/hour
- Setup time: ~15 minutes ($0.05)
- Testing time: ~10 minutes for 3 files ($0.03)
- Total expected: ~$0.50 + buffer = $1.00 budget

---

## File Locations

**GPU Pipeline Implementation:**
- `src/pipeline_gpu.py` - Main GPU pipeline (230 lines)
- `src/gpu_config.py` - Provider detection and optimization (187 lines)
- `src/gpu_audio_ops.py` - GPU audio preprocessing (211 lines)

**Setup Scripts:**
- `scripts/setup_gpu.sh` - Automated GPU environment setup
- `scripts/setup_vast_api.sh` - Vast.ai API key configuration

**Test Files:**
- `test_gpu_validation.py` - GPU environment validation
- `test_pytorch_detailed.py` - PyTorch/CUDA detailed checks

**Sample Audio Files (to copy to Vast.ai):**
- `tests/samples/Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3`
- `tests/samples/LIVE Cognitive Behavioral Therapy Session (1).mp3`
- `tests/samples/Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3`

**CPU Baseline Results (for comparison):**
- `tests/outputs/FINAL_TEST_SUMMARY.md` - Complete CPU test results
- `tests/outputs/PIPELINE_PERFORMANCE_REPORT.json` - CPU metrics

---

## Expected GPU Configuration (from gpu_config.py)

When Vast.ai provider is detected:

```python
GPUConfig(
    provider=GPUProvider.VASTAI,
    device_name="NVIDIA GeForce RTX 3090",
    vram_gb=24.0,
    compute_type="int8",          # Optimized for RTX 3090
    batch_size=8,                  # Balanced throughput
    num_workers=4,
    enable_tf32=False,             # cuDNN compatibility
    model_cache_dir="/workspace/models"  # Persistent storage
)
```

---

## Safety Checklist

Before running orchestrator:

- [ ] Vast.ai CLI is installed (`vastai --version`)
- [ ] Vast.ai account has credit ($5-10 recommended)
- [ ] SSH key is configured for Vast.ai
- [ ] `.env` file has HF_TOKEN for pyannote models
- [ ] CPU baseline results are saved (for comparison)
- [ ] Budget limit is clear ($1.00 max expected)

After testing completes:

- [ ] Instance is destroyed (`vastai destroy instance <ID>`)
- [ ] Billing has stopped (check Vast.ai dashboard)
- [ ] Test results are downloaded locally
- [ ] GPU validation report is generated

---

## Copy This Prompt

Copy the text between the triple backticks above and run:

```bash
/cl:orchestrate [paste the prompt here]
```

The orchestrator will handle:
1. Launching Vast.ai instance
2. Setting up GPU environment
3. Running GPU pipeline tests
4. Generating comparison report
5. Destroying instance

Total time: ~1-2 hours
Total cost: ~$0.50-1.00
