#!/bin/bash
#
# Run GPU pipeline and automatically display diarized transcript
#
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AUDIO_FILE="$1"

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: $0 <audio_file>"
    exit 1
fi

# Update VAST_API_KEY in .env if provided as environment variable
if [ ! -z "$VAST_API_KEY" ]; then
    echo "VAST_API_KEY=$VAST_API_KEY" > .env.tmp
    grep -v "VAST_API_KEY" .env >> .env.tmp || true
    mv .env.tmp .env
    echo -e "${GREEN}✓ Updated VAST_API_KEY in .env${NC}"
fi

# Run the parallel GPU race
echo -e "${BLUE}Starting GPU parallel processing...${NC}\n"
./run_gpu_parallel.sh "$AUDIO_FILE" 2 2

# Find the most recent result file
RESULT_FILE=$(find outputs/vast_results -name "*.json" -type f -print0 2>/dev/null | xargs -0 ls -t | head -1)

if [ -z "$RESULT_FILE" ]; then
    echo -e "${YELLOW}Warning: Could not find result file${NC}"
    exit 1
fi

echo -e "\n${GREEN}${'='*60}${NC}"
echo -e "${GREEN}RESULTS & METRICS${NC}"
echo -e "${GREEN}${'='*60}${NC}\n"

# Display metrics using Python
python3 << EOF
import json
from pathlib import Path

# Load results
with open("$RESULT_FILE") as f:
    data = json.load(f)

# Performance metrics
perf = data.get('performance', {})
print("⏱️  PERFORMANCE METRICS")
print("=" * 60)
print(f"Audio Duration:      {perf.get('audio_duration_seconds', 0):.1f}s ({perf.get('audio_duration_seconds', 0)/60:.1f} min)")
print(f"Total Processing:    {perf.get('total_time_seconds', 0):.1f}s ({perf.get('total_time_seconds', 0)/60:.1f} min)")
print(f"Speedup:             {perf.get('audio_duration_seconds', 1) / max(perf.get('total_time_seconds', 1), 1):.2f}x real-time")
print()

# Stage breakdown
stages = perf.get('stages', {})
if stages:
    print("📊 STAGE BREAKDOWN")
    print("=" * 60)
    for stage, time in stages.items():
        print(f"{stage:20s} {time:8.2f}s")
    print()

# GPU metrics
gpu = perf.get('gpu_metrics', {})
if gpu:
    print("🎮 GPU METRICS")
    print("=" * 60)
    print(f"Provider:            {gpu.get('provider', 'unknown')}")
    print(f"Device:              {gpu.get('device', 'unknown')}")
    print(f"Peak VRAM:           {gpu.get('peak_vram_gb', 0):.1f} GB")
    print(f"Avg Utilization:     {gpu.get('avg_utilization_pct', 0):.1f}%")
    print()

# Cost estimate (approximate)
cost_per_hour = 0.35  # Average L4 cost
processing_hours = perf.get('total_time_seconds', 0) / 3600
estimated_cost = processing_hours * cost_per_hour
print("💰 COST ESTIMATE")
print("=" * 60)
print(f"Processing Time:     {perf.get('total_time_seconds', 0)/60:.1f} minutes")
print(f"Estimated Cost:      \${estimated_cost:.4f} (@ \${cost_per_hour:.2f}/hr)")
print()

# Transcript statistics
segments = data.get('aligned_transcript', []) or data.get('transcript', [])
print("📝 TRANSCRIPT STATISTICS")
print("=" * 60)
print(f"Total Segments:      {len(segments)}")

# Count speakers
speakers = {}
for seg in segments:
    speaker = seg.get('speaker', 'Unknown')
    speakers[speaker] = speakers.get(speaker, 0) + 1

for speaker, count in sorted(speakers.items()):
    print(f"{speaker:20s} {count} segments")
print()

# Display diarized transcript
print("\n" + "=" * 60)
print("📋 DIARIZED TRANSCRIPT")
print("=" * 60 + "\n")

current_speaker = None
for i, seg in enumerate(segments[:50]):  # Show first 50 segments
    speaker = seg.get('speaker', 'Unknown')
    text = seg.get('text', '').strip()
    start = seg.get('start', 0)

    # Add speaker label when speaker changes
    if speaker != current_speaker:
        print(f"\n[{speaker}] ({start:.1f}s)")
        current_speaker = speaker

    print(f"  {text}")

if len(segments) > 50:
    print(f"\n... ({len(segments) - 50} more segments)")
    print(f"\nFull transcript saved to: $RESULT_FILE")

print("\n" + "=" * 60)
EOF

echo -e "\n${GREEN}✓ Complete! Full results saved to:${NC}"
echo -e "${BLUE}$RESULT_FILE${NC}\n"
