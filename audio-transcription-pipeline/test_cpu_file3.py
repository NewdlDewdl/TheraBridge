#!/usr/bin/env python3
"""
CPU Pipeline Test - File 3: Carl Rogers & Gloria (45.7 min)
============================================================
Tests CPU/API pipeline with longest audio file, includes chunking validation.
"""

import os
import sys
import json
import time
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pydub import AudioSegment
from openai import OpenAI

# ============================================================================
# Preprocessing (with file size check)
# ============================================================================
def preprocess_audio(audio_path: str, output_path: str) -> Dict:
    """Preprocess audio and return metadata"""
    print("\n[STAGE 1: PREPROCESSING]")
    print(f"Input: {audio_path}")

    start_time = time.time()

    # Load audio
    audio = AudioSegment.from_file(audio_path)
    original_duration = len(audio) / 1000
    print(f"Duration: {original_duration:.1f}s ({original_duration/60:.1f} minutes)")

    # Trim silence
    from pydub.silence import detect_leading_silence
    start_trim = detect_leading_silence(audio, silence_threshold=-40)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=-40)
    duration_ms = len(audio)
    audio = audio[start_trim:duration_ms - end_trim]

    # Normalize
    from pydub import effects
    audio = effects.normalize(audio, headroom=0.1)

    # Convert to mono 16kHz
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    # Export as MP3
    audio.export(output_path, format="mp3", bitrate="64k")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    preprocess_time = time.time() - start_time

    print(f"Output: {output_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"Preprocessing time: {preprocess_time:.2f}s")

    return {
        "duration": original_duration,
        "file_size_mb": file_size_mb,
        "preprocess_time": preprocess_time,
        "needs_chunking": file_size_mb > 24
    }

# ============================================================================
# Chunking (if needed)
# ============================================================================
def split_audio_chunks(audio_path: str, chunk_minutes: int = 10) -> List[str]:
    """Split audio into chunks if >24MB"""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if file_size_mb <= 24:
        print(f"\n[CHUNKING] Not needed ({file_size_mb:.1f}MB < 24MB)")
        return [audio_path]

    print(f"\n[CHUNKING] Required ({file_size_mb:.1f}MB > 24MB)")
    print(f"Splitting into {chunk_minutes}-minute chunks...")

    audio = AudioSegment.from_file(audio_path)
    chunk_length_ms = chunk_minutes * 60 * 1000

    chunks = []
    chunk_dir = Path(audio_path).parent

    for i, start_ms in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start_ms:start_ms + chunk_length_ms]
        chunk_path = str(chunk_dir / f"chunk_{i:03d}.mp3")
        chunk.export(chunk_path, format="mp3", bitrate="64k")

        chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
        chunks.append(chunk_path)
        print(f"  Chunk {i}: {start_ms/1000:.1f}s - {(start_ms + len(chunk))/1000:.1f}s ({chunk_size_mb:.2f}MB)")

    print(f"Created {len(chunks)} chunks")
    return chunks

# ============================================================================
# Whisper Transcription
# ============================================================================
def transcribe_with_whisper(audio_path: str) -> Dict:
    """Transcribe using OpenAI Whisper API with chunking support"""
    print("\n[STAGE 2: WHISPER TRANSCRIPTION]")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Check if chunking needed
    chunks = split_audio_chunks(audio_path)

    all_segments = []
    full_text_parts = []
    time_offset = 0.0
    total_api_time = 0.0
    detected_language = None

    for i, chunk_path in enumerate(chunks):
        print(f"\n[WHISPER] Transcribing chunk {i+1}/{len(chunks)}...")

        chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
        print(f"  File: {chunk_path}")
        print(f"  Size: {chunk_size_mb:.2f}MB")

        api_start = time.time()

        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        api_time = time.time() - api_start
        total_api_time += api_time

        print(f"  API latency: {api_time:.2f}s")
        print(f"  Segments: {len(response.segments)}")
        print(f"  Duration: {response.duration:.1f}s")

        # Adjust timestamps by offset
        for seg in response.segments:
            all_segments.append({
                "start": seg.start + time_offset,
                "end": seg.end + time_offset,
                "text": seg.text.strip()
            })

        full_text_parts.append(response.text)
        detected_language = response.language
        time_offset += response.duration

        # Cleanup chunk files (except original)
        if chunk_path != audio_path:
            os.remove(chunk_path)

    print(f"\n[WHISPER] Complete!")
    print(f"  Total segments: {len(all_segments)}")
    print(f"  Total duration: {time_offset:.1f}s")
    print(f"  Total API time: {total_api_time:.2f}s")

    return {
        "segments": all_segments,
        "full_text": " ".join(full_text_parts),
        "language": detected_language,
        "duration": time_offset,
        "num_chunks": len(chunks),
        "api_latency": total_api_time
    }

# ============================================================================
# Speaker Diarization
# ============================================================================
def diarize_speakers(audio_path: str) -> List[Dict]:
    """Run pyannote speaker diarization"""
    print("\n[STAGE 3: SPEAKER DIARIZATION]")

    import torch
    from pyannote.audio import Pipeline
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    import torchaudio
    from pyannote_compat import extract_annotation

    # Add safe globals for PyTorch compatibility
    torch.serialization.add_safe_globals([
        torch.torch_version.TorchVersion,
        Specifications,
        Problem,
        Resolution
    ])

    # Setup device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    # Load model
    hf_token = os.getenv("HF_TOKEN")
    print("Loading pyannote model...")
    model_start = time.time()

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )
    pipeline.to(device)

    print(f"Model loaded in {time.time() - model_start:.2f}s")

    # Run diarization
    print("Running diarization...")
    diarize_start = time.time()

    waveform, sample_rate = torchaudio.load(audio_path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    audio_input = {"waveform": waveform, "sample_rate": sample_rate}
    diarization = pipeline(audio_input, num_speakers=2)

    # Extract annotation using compatibility layer
    annotation = extract_annotation(diarization)

    # Convert to speaker turns
    turns = []
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        turns.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end
        })

    diarize_time = time.time() - diarize_start

    # Stats
    speaker_counts = {}
    for t in turns:
        speaker_counts[t["speaker"]] = speaker_counts.get(t["speaker"], 0) + 1

    print(f"Diarization time: {diarize_time:.2f}s")
    print(f"Speaker turns: {len(turns)}")
    print(f"Speaker distribution: {speaker_counts}")

    return {
        "turns": turns,
        "diarize_time": diarize_time
    }

# ============================================================================
# Alignment
# ============================================================================
def align_speakers(segments: List[Dict], turns: List[Dict]) -> List[Dict]:
    """Align transcription segments with speaker turns"""
    print("\n[STAGE 4: ALIGNMENT]")

    aligned = []
    for seg in segments:
        seg_start, seg_end = seg["start"], seg["end"]
        seg_duration = seg_end - seg_start

        # Find best overlapping speaker
        best_speaker = "UNKNOWN"
        best_overlap = 0

        for turn in turns:
            overlap_start = max(seg_start, turn["start"])
            overlap_end = min(seg_end, turn["end"])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        # Require 50% overlap
        if seg_duration > 0 and (best_overlap / seg_duration) < 0.5:
            best_speaker = "UNKNOWN"

        aligned.append({
            "start": seg_start,
            "end": seg_end,
            "text": seg["text"],
            "speaker": best_speaker
        })

    # Calculate alignment quality
    unknown_count = sum(1 for s in aligned if s["speaker"] == "UNKNOWN")
    unknown_pct = (unknown_count / len(aligned) * 100) if aligned else 0

    speaker_counts = {}
    for seg in aligned:
        speaker_counts[seg["speaker"]] = speaker_counts.get(seg["speaker"], 0) + 1

    print(f"Aligned segments: {len(aligned)}")
    print(f"Speaker distribution: {speaker_counts}")
    print(f"Unknown segments: {unknown_count} ({unknown_pct:.1f}%)")

    return aligned

# ============================================================================
# Main Test
# ============================================================================
def main():
    print("="*70)
    print("CPU PIPELINE TEST - FILE 3: Carl Rogers & Gloria (45.7 min)")
    print("="*70)

    # Test file
    audio_file = Path("/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/tests/samples/Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3")

    if not audio_file.exists():
        print(f"ERROR: File not found: {audio_file}")
        return

    # Prepare output directory
    output_dir = Path(__file__).parent / "tests" / "outputs"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Track overall time and memory
    total_start = time.time()
    process = psutil.Process()
    mem_start = process.memory_info().rss / (1024 * 1024)  # MB

    # Step 1: Preprocess
    processed_path = output_dir / "temp_processed.mp3"
    preprocess_meta = preprocess_audio(str(audio_file), str(processed_path))

    # Step 2: Transcribe (with chunking if needed)
    transcription = transcribe_with_whisper(str(processed_path))

    # Step 3: Diarize
    diarization = diarize_speakers(str(processed_path))

    # Step 4: Align
    aligned_segments = align_speakers(transcription["segments"], diarization["turns"])

    # Calculate metrics
    total_time = time.time() - total_start
    mem_end = process.memory_info().rss / (1024 * 1024)
    mem_used = mem_end - mem_start

    speed_ratio = preprocess_meta["duration"] / total_time if total_time > 0 else 0
    unknown_count = sum(1 for s in aligned_segments if s["speaker"] == "UNKNOWN")
    unknown_pct = (unknown_count / len(aligned_segments) * 100) if aligned_segments else 0

    # Print summary
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"File: {audio_file.name}")
    print(f"Duration: {preprocess_meta['duration']:.1f}s ({preprocess_meta['duration']/60:.1f} min)")
    print(f"Chunking: {'YES (' + str(transcription['num_chunks']) + ' chunks)' if transcription['num_chunks'] > 1 else 'NO'}")
    print(f"\nTiming:")
    print(f"  Preprocessing: {preprocess_meta['preprocess_time']:.2f}s")
    print(f"  Whisper API: {transcription['api_latency']:.2f}s")
    print(f"  Diarization: {diarization['diarize_time']:.2f}s")
    print(f"  Total: {total_time:.2f}s")
    print(f"  Speed ratio: {speed_ratio:.2f}x real-time")
    print(f"\nOutput:")
    print(f"  Segments: {len(aligned_segments)}")
    print(f"  Speaker turns: {len(diarization['turns'])}")
    print(f"  Unknown segments: {unknown_count} ({unknown_pct:.1f}%)")
    print(f"\nMemory:")
    print(f"  Peak usage: {mem_end:.1f} MB")
    print(f"  Delta: +{mem_used:.1f} MB")

    # Save output JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"cpu_pipeline_file3_{timestamp}.json"

    output_data = {
        "metadata": {
            "source_file": str(audio_file),
            "test_id": "cpu_pipeline_file3",
            "timestamp": timestamp,
            "duration": preprocess_meta["duration"],
            "language": transcription["language"],
            "chunking_used": transcription["num_chunks"] > 1,
            "num_chunks": transcription["num_chunks"]
        },
        "performance": {
            "preprocess_time_seconds": preprocess_meta["preprocess_time"],
            "api_latency_seconds": transcription["api_latency"],
            "diarization_time_seconds": diarization["diarize_time"],
            "total_time_seconds": total_time,
            "speed_ratio": speed_ratio,
            "memory_mb": {
                "start": mem_start,
                "end": mem_end,
                "delta": mem_used
            }
        },
        "quality": {
            "num_segments": len(aligned_segments),
            "num_speaker_turns": len(diarization["turns"]),
            "unknown_segments": unknown_count,
            "unknown_percentage": unknown_pct
        },
        "segments": transcription["segments"],
        "speaker_turns": diarization["turns"],
        "diarized_segments": aligned_segments,
        "full_text": transcription["full_text"]
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nOutput saved to: {output_file}")

    # Save performance summary
    perf_file = output_dir / f"cpu_pipeline_file3_{timestamp}_performance.json"
    perf_data = {
        "test_id": "cpu_pipeline_file3",
        "file": audio_file.name,
        "duration_seconds": preprocess_meta["duration"],
        "chunking_used": transcription["num_chunks"] > 1,
        "num_chunks": transcription["num_chunks"],
        "total_time_seconds": total_time,
        "api_latency_seconds": transcription["api_latency"],
        "speed_ratio": speed_ratio,
        "segments": len(aligned_segments),
        "speaker_turns": len(diarization["turns"]),
        "unknown_percentage": unknown_pct,
        "memory_mb": mem_used,
        "status": "PASS" if unknown_pct < 30 else "FAIL - High unknown %"
    }

    with open(perf_file, "w") as f:
        json.dump(perf_data, f, indent=2)

    print(f"Performance summary: {perf_file}")

    # Cleanup
    if processed_path.exists():
        processed_path.unlink()

    # Final status
    print("\n" + "="*70)
    status = "PASS" if unknown_pct < 30 else f"FAIL (Unknown {unknown_pct:.1f}% > 30%)"
    print(f"TEST STATUS: {status}")
    print("="*70)

if __name__ == "__main__":
    main()
