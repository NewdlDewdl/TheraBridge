#!/usr/bin/env python3
"""
Audio Transcription Pipeline
============================

Complete pipeline for audio processing:
1. Audio input/upload
2. Preprocessing (format conversion, noise reduction)
3. Whisper transcription
4. Post-processing (text cleanup, formatting)
5. Speaker diarization
6. Parsing and structuring
7. UX output formatting
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Audio processing imports (to be installed)
# from pydub import AudioSegment
# from faster_whisper import WhisperModel
# import pyannote.audio  # for diarization

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata"""
    segments: List[TranscriptionSegment]
    full_text: str
    duration: float
    language: str
    metadata: Dict

class AudioPreprocessor:
    """Handles audio preprocessing before transcription"""


    # Preprocessing parameters
    def __init__(self,
                 target_format: str = "mp3",
                 target_sample_rate: int = 16000,
                 target_bitrate: str = "64k",
                 max_file_size_mb: int = 25):
        self.target_format = target_format
        self.target_sample_rate = target_sample_rate
        self.target_bitrate = target_bitrate
        self.max_file_size_mb = max_file_size_mb

    # Preprocess audio file
    def preprocess(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Preprocess audio file for optimal Whisper transcription

        Steps:
        1. Load audio file
        2. Trim leading/trailing silence
        3. Normalize volume
        4. Convert to target format (16kHz mono MP3)
        5. Validate file size

        Returns: Path to processed audio file
        """
        from pydub import AudioSegment, effects
        from pydub.silence import detect_leading_silence

        print(f"[Preprocess] Loading: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        original_duration = len(audio) / 1000  # seconds
        print(f"[Preprocess] Duration: {original_duration:.1f}s")

        # Step 1: Trim silence
        audio = self._trim_silence(audio)

        # Step 2: Normalize volume
        audio = self._normalize(audio)

        # Step 3: Convert format
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(self.target_sample_rate)  # 16kHz

        # Step 4: Export
        if output_path is None:
            output_path = audio_path.rsplit('.', 1)[0] + f'_processed.{self.target_format}'

        audio.export(
            output_path,
            format=self.target_format,
            bitrate=self.target_bitrate,
            parameters=["-ac", "1"]
        )

        # Step 5: Validate size
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[Preprocess] Output: {output_path} ({file_size_mb:.2f} MB)")

        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File size {file_size_mb:.2f}MB exceeds {self.max_file_size_mb}MB limit")

        return output_path

    def _trim_silence(self, audio: 'AudioSegment',
                      silence_threshold: int = -40,
                      min_silence_len: int = 500) -> 'AudioSegment':
        """Remove leading and trailing silence"""
        from pydub.silence import detect_leading_silence

        start_trim = detect_leading_silence(audio, silence_threshold=silence_threshold)
        end_trim = detect_leading_silence(audio.reverse(), silence_threshold=silence_threshold)

        duration = len(audio)
        trimmed = audio[start_trim:duration - end_trim]

        trimmed_amount = (start_trim + end_trim) / 1000
        if trimmed_amount > 0:
            print(f"[Preprocess] Trimmed {trimmed_amount:.1f}s of silence")

        return trimmed

    def _normalize(self, audio: 'AudioSegment', target_dBFS: float = -20.0) -> 'AudioSegment':
        """Normalize audio to target volume level"""
        from pydub import effects

        # Use pydub's normalize (peaks at 0dB with headroom)
        normalized = effects.normalize(audio, headroom=0.1)

        change = normalized.dBFS - audio.dBFS
        if abs(change) > 0.5:
            print(f"[Preprocess] Normalized volume: {change:+.1f} dB")

        return normalized

    def validate_audio(self, audio_path: str) -> Dict:
        """Validate audio file before processing"""
        from pydub import AudioSegment

        try:
            audio = AudioSegment.from_file(audio_path)
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

            return {
                "valid": True,
                "duration_seconds": len(audio) / 1000,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "file_size_mb": file_size_mb,
                "format": audio_path.rsplit('.', 1)[-1].lower()
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def preprocess_long_audio(self, audio_path: str, output_dir: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Preprocess long audio files by splitting into chunks for Whisper API.

        Uses silence detection to find natural break points (conversation pauses).
        Each chunk is exported as a separate file under the 25MB limit.

        Args:
            audio_path: Path to the input audio file
            output_dir: Directory to save chunks (default: same as input)

        Returns:
            List of tuples: [(chunk_path, start_offset_seconds), ...]
            The offset is needed to adjust timestamps when merging transcriptions.
        """
        from pydub import AudioSegment
        from pydub.silence import split_on_silence

        print(f"[Preprocess] Loading long audio: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        duration_min = len(audio) / 1000 / 60
        print(f"[Preprocess] Duration: {duration_min:.1f} minutes")

        # Normalize and convert format first
        audio = self._normalize(audio)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(self.target_sample_rate)

        # Calculate target chunk duration based on bitrate
        # At 64kbps, we get ~0.46 MB/min, so 20MB = ~43 min (safe margin under 25MB)
        target_chunk_mb = 20  # Leave 5MB buffer
        mb_per_min = 0.46
        target_chunk_duration_ms = int((target_chunk_mb / mb_per_min) * 60 * 1000)

        print(f"[Preprocess] Target chunk duration: {target_chunk_duration_ms / 1000 / 60:.1f} minutes")

        # Split audio into chunks at silence points
        chunks_with_offsets = self._split_at_silence(audio, target_chunk_duration_ms)

        # Export each chunk
        if output_dir is None:
            output_dir = os.path.dirname(audio_path) or "."

        base_name = os.path.basename(audio_path).rsplit('.', 1)[0]
        chunk_paths = []

        for i, (chunk, offset_ms) in enumerate(chunks_with_offsets):
            chunk_path = os.path.join(output_dir, f"{base_name}_chunk_{i:03d}.{self.target_format}")

            chunk.export(
                chunk_path,
                format=self.target_format,
                bitrate=self.target_bitrate,
                parameters=["-ac", "1"]
            )

            chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
            chunk_duration = len(chunk) / 1000
            offset_sec = offset_ms / 1000

            print(f"[Preprocess] Chunk {i}: {chunk_duration:.1f}s, {chunk_size_mb:.2f}MB, offset={offset_sec:.1f}s")
            chunk_paths.append((chunk_path, offset_sec))

        print(f"[Preprocess] Created {len(chunk_paths)} chunks")
        return chunk_paths

    def _split_at_silence(self, audio: 'AudioSegment', target_duration_ms: int) -> List[Tuple['AudioSegment', int]]:
        """
        Split audio into chunks at natural silence points (conversation pauses).

        Optimized for therapy sessions where natural pauses occur between
        therapist/patient exchanges (typically 500ms-2s).

        Args:
            audio: The audio to split
            target_duration_ms: Target duration for each chunk in milliseconds

        Returns:
            List of tuples: [(audio_chunk, start_offset_ms), ...]
        """
        from pydub.silence import detect_silence

        # Therapy-optimized parameters:
        # - silence_thresh: -40dB catches natural conversation pauses without
        #   picking up breathing or soft background noise
        # - min_silence_len: 700ms ensures we only split at meaningful pauses
        #   (therapist waiting for response, patient thinking, etc.)
        # - keep_silence: 300ms at boundaries for natural-sounding chunks
        silence_thresh = -40  # dB
        min_silence_len = 700  # ms - typical therapy pause length
        keep_silence = 300  # ms to keep at chunk boundaries

        total_duration = len(audio)

        # If audio is short enough, return as single chunk
        if total_duration <= target_duration_ms:
            print(f"[Preprocess] Audio under target duration, no splitting needed")
            return [(audio, 0)]

        # Detect all silence regions: returns list of [start_ms, end_ms]
        print(f"[Preprocess] Detecting silence regions...")
        silences = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        print(f"[Preprocess] Found {len(silences)} silence regions")

        # If no silences found, fall back to fixed-duration splits
        if not silences:
            print(f"[Preprocess] No silences detected, using fixed-duration splits")
            return self._split_fixed_duration(audio, target_duration_ms)

        # Build chunks by accumulating audio until we approach target duration,
        # then splitting at the nearest silence point
        chunks = []
        current_start = 0

        while current_start < total_duration:
            # Calculate ideal end point
            ideal_end = current_start + target_duration_ms

            # If this would be the last chunk, take the rest
            if ideal_end >= total_duration:
                chunks.append((audio[current_start:], current_start))
                break

            # Find the best silence point near our ideal end
            # Look for silences within a window around the target duration
            window_start = ideal_end - (5 * 60 * 1000)  # 5 min before target
            window_end = ideal_end + (2 * 60 * 1000)    # 2 min after target (stay under limit)

            best_split = None
            for silence_start, silence_end in silences:
                # Get midpoint of silence (cleanest split point)
                silence_mid = (silence_start + silence_end) // 2

                # Check if this silence is in our search window
                if window_start <= silence_mid <= window_end:
                    # Prefer silences closer to (but not exceeding) ideal_end
                    if best_split is None:
                        best_split = silence_mid
                    elif silence_mid <= ideal_end and silence_mid > best_split:
                        # Prefer later splits that don't exceed target
                        best_split = silence_mid
                    elif best_split > ideal_end and silence_mid < best_split:
                        # If we're already over, prefer earlier splits
                        best_split = silence_mid

            # If no good silence found, use ideal_end (may cut mid-sentence)
            if best_split is None:
                print(f"[Preprocess] Warning: No silence found near {ideal_end/1000:.1f}s, using fixed split")
                best_split = ideal_end

            # Extract chunk with some silence padding for smooth transitions
            chunk_end = min(best_split + keep_silence, total_duration)
            chunk = audio[current_start:chunk_end]
            chunks.append((chunk, current_start))

            # Next chunk starts at split point (slight overlap is fine)
            current_start = best_split

        print(f"[Preprocess] Split into {len(chunks)} chunks at natural pauses")
        return chunks

    def _split_fixed_duration(self, audio: 'AudioSegment', target_duration_ms: int) -> List[Tuple['AudioSegment', int]]:
        """Fallback: split at fixed intervals if no silences detected."""
        chunks = []
        current_start = 0
        total_duration = len(audio)

        while current_start < total_duration:
            chunk_end = min(current_start + target_duration_ms, total_duration)
            chunks.append((audio[current_start:chunk_end], current_start))
            current_start = chunk_end

        return chunks

class WhisperTranscriber:
    """Handles OpenAI Whisper API transcription"""

    def __init__(self, api_key: Optional[str] = None):
        from openai import OpenAI
        from dotenv import load_dotenv

        load_dotenv()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=self.api_key)

    def transcribe(self,
                   audio_path: str,
                   language: Optional[str] = "en",
                   response_format: str = "verbose_json") -> Dict:
        """
        Transcribe audio using OpenAI Whisper API

        Args:
            audio_path: Path to audio file (must be <25MB)
            language: Language code (default: "en")
            response_format: "json", "text", "verbose_json", "srt", "vtt"

        Returns:
            Dict with segments, full text, language, and duration
        """
        print(f"[Whisper] Transcribing: {audio_path}")

        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"[Whisper] File size: {file_size_mb:.2f} MB")

        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format,
                timestamp_granularities=["segment"] if response_format == "verbose_json" else None
            )

        # Parse response based on format
        if response_format == "verbose_json":
            result = {
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip()
                    }
                    for seg in response.segments
                ],
                "full_text": response.text,
                "language": response.language,
                "duration": response.duration
            }
        elif response_format == "json":
            result = {
                "segments": [],
                "full_text": response.text,
                "language": language,
                "duration": None
            }
        else:
            result = {
                "segments": [],
                "full_text": response,
                "language": language,
                "duration": None
            }

        print(f"[Whisper] Transcribed {len(result['segments'])} segments")
        return result

    def transcribe_chunks(self, chunks: List[Tuple[str, float]], language: Optional[str] = "en") -> Dict:
        """
        Transcribe multiple audio chunks and merge results with adjusted timestamps.

        Args:
            chunks: List of tuples [(chunk_path, offset_seconds), ...]
                    offset_seconds is the start time of this chunk in the original audio
            language: Language code (default: "en")

        Returns:
            Merged Dict with all segments (timestamps adjusted to original timeline),
            combined full text, language, and total duration
        """
        print(f"[Whisper] Transcribing {len(chunks)} chunks...")

        all_segments = []
        all_text_parts = []
        total_duration = 0

        for i, (chunk_path, offset_sec) in enumerate(chunks):
            print(f"[Whisper] Processing chunk {i + 1}/{len(chunks)}...")

            # Transcribe this chunk
            chunk_result = self.transcribe(chunk_path, language=language)

            # Adjust timestamps by adding the offset
            for segment in chunk_result["segments"]:
                adjusted_segment = {
                    "start": segment["start"] + offset_sec,
                    "end": segment["end"] + offset_sec,
                    "text": segment["text"]
                }
                all_segments.append(adjusted_segment)

            all_text_parts.append(chunk_result["full_text"])

            # Track total duration (last chunk's end time)
            if chunk_result["segments"]:
                last_seg = chunk_result["segments"][-1]
                chunk_end_time = last_seg["end"] + offset_sec
                total_duration = max(total_duration, chunk_end_time)

        # Merge results
        merged_result = {
            "segments": all_segments,
            "full_text": " ".join(all_text_parts),
            "language": language,
            "duration": total_duration
        }

        print(f"[Whisper] Merged {len(all_segments)} total segments from {len(chunks)} chunks")
        print(f"[Whisper] Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
        return merged_result

class PostProcessor:
    """Handles post-processing of transcribed text"""

    # Common Whisper hallucinations to remove
    HALLUCINATIONS = [
        "Thank you for watching.",
        "Thanks for watching.",
        "Thank you for listening.",
        "Please subscribe.",
        "Like and subscribe.",
        "See you next time.",
        "See you in the next video.",
        "Don't forget to subscribe.",
        "Hit the bell icon.",
        "Leave a comment below.",
        "[Music]",
        "[Applause]",
        "(music)",
        "(applause)",
        "...",
        "you",  # Single word artifacts
    ]

    def __init__(self):
        self.hallucinations = [h.lower() for h in self.HALLUCINATIONS]

    def process(self, transcription_data: Dict) -> Dict:
        """
        Clean and format transcribed text

        Steps:
        1. Remove hallucinations
        2. Clean individual segments (with smart capitalization)
        3. Rebuild full text
        """
        print("[PostProcess] Cleaning transcription...")

        cleaned_segments = []
        prev_ended_sentence = True  # First segment should be capitalized

        for segment in transcription_data.get("segments", []):
            cleaned_text = self._clean_text(segment["text"], capitalize=prev_ended_sentence)

            # Skip empty segments or hallucinations
            if cleaned_text and not self._is_hallucination(cleaned_text):
                cleaned_segments.append({
                    **segment,
                    "text": cleaned_text
                })
                # Check if this segment ends a sentence
                prev_ended_sentence = cleaned_text.rstrip()[-1] in ".!?" if cleaned_text.rstrip() else False

        # Rebuild full text from cleaned segments
        full_text = " ".join([s["text"] for s in cleaned_segments])

        removed_count = len(transcription_data.get("segments", [])) - len(cleaned_segments)
        if removed_count > 0:
            print(f"[PostProcess] Removed {removed_count} empty/hallucinated segments")

        print(f"[PostProcess] Cleaned {len(cleaned_segments)} segments")

        return {
            **transcription_data,
            "segments": cleaned_segments,
            "full_text": full_text
        }

    def _clean_text(self, text: str, capitalize: bool = False) -> str:
        """Clean individual text segment

        Args:
            text: The text to clean
            capitalize: Whether to capitalize first letter (True if previous segment ended with .!?)
        """
        if not text:
            return ""

        text = text.strip()

        # Fix double spaces
        while "  " in text:
            text = text.replace("  ", " ")

        # Smart capitalization: only capitalize if previous segment ended a sentence
        if capitalize and text and text[0].islower():
            text = text[0].upper() + text[1:]

        return text

    def _is_hallucination(self, text: str) -> bool:
        """Check if text is a known Whisper hallucination"""
        text_lower = text.lower().strip()

        # Check exact matches and partial matches
        for h in self.hallucinations:
            if text_lower == h or (len(h) > 5 and h in text_lower):
                return True

        # Also filter very short segments (likely artifacts)
        if len(text_lower) < 3:
            return True

        return False

class SpeakerDiarizer:
    """Handles speaker diarization using Pyannote Audio"""

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize Pyannote Audio pipeline for speaker diarization.

        Args:
            hf_token: HuggingFace API token (or reads from HF_TOKEN env var)
        """
        import torch
        from pyannote.audio import Pipeline
        from dotenv import load_dotenv

        load_dotenv()

        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        if not self.hf_token:
            raise ValueError(
                "HF_TOKEN not found. Please set it in .env or pass to __init__. "
                "Get token at https://hf.co/settings/tokens and accept terms at "
                "https://huggingface.co/pyannote/speaker-diarization-3.1"
            )

        print("[Diarization] Loading Pyannote speaker-diarization-3.1 model...")
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )

        # Use GPU if available for faster processing
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.pipeline.to(self.device)
        print(f"[Diarization] Using device: {self.device}")

        # Default settings optimized for therapy sessions
        self.num_speakers = 2  # Therapist + Client
        self.min_speakers = 2
        self.max_speakers = 2

    def diarize(self, audio_path: str, transcription_data: Dict) -> Dict:
        """
        Identify speakers and assign to transcription segments.

        Process:
        1. Run Pyannote diarization on audio file
        2. Extract speaker turns with timestamps
        3. Align speaker labels with Whisper transcription segments
        4. Add "speaker" field to each segment

        Args:
            audio_path: Path to audio file (preprocessed)
            transcription_data: Dict with "segments" list from Whisper

        Returns:
            Same Dict with "speaker" field added to each segment
        """
        print("[Diarization] Running speaker diarization...")

        # Step 1: Run Pyannote diarization
        # For therapy sessions, we know there are exactly 2 speakers
        diarization_result = self.pipeline(
            audio_path,
            num_speakers=self.num_speakers
        )

        # Step 2: Extract speaker turns
        speaker_turns = []
        for turn, _, speaker_label in diarization_result.itertracks(yield_label=True):
            speaker_turns.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker_label  # e.g., "SPEAKER_00", "SPEAKER_01"
            })

        print(f"[Diarization] Detected {len(speaker_turns)} speaker turns")

        # Step 3: Align speaker labels with transcription segments
        segments = transcription_data.get("segments", [])
        aligned_segments = self._align_speakers_with_segments(segments, speaker_turns)

        # Step 4: Update transcription data
        transcription_data["segments"] = aligned_segments

        # Add metadata about speakers
        unique_speakers = set(seg.get("speaker", "UNKNOWN") for seg in aligned_segments)
        print(f"[Diarization] Identified {len(unique_speakers)} unique speakers")

        return transcription_data

    def _align_speakers_with_segments(
        self,
        transcription_segments: List[Dict],
        speaker_turns: List[Dict]
    ) -> List[Dict]:
        """
        Align Whisper transcription segments with Pyannote speaker turns.

        Uses temporal overlap matching: assigns each segment to the speaker
        with the greatest time overlap.

        Args:
            transcription_segments: Whisper segments with start/end/text
            speaker_turns: Pyannote turns with start/end/speaker

        Returns:
            Segments with "speaker" field added
        """
        aligned = []

        for segment in transcription_segments:
            seg_start = segment["start"]
            seg_end = segment["end"]

            # Find speaker with maximum temporal overlap
            best_speaker = None
            max_overlap = 0.0

            for turn in speaker_turns:
                # Calculate overlap duration
                overlap_start = max(seg_start, turn["start"])
                overlap_end = min(seg_end, turn["end"])
                overlap_duration = max(0, overlap_end - overlap_start)

                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    best_speaker = turn["speaker"]

            # Add speaker label to segment
            aligned.append({
                **segment,
                "speaker": best_speaker if best_speaker else "UNKNOWN"
            })

        return aligned

    def map_therapy_speakers(
        self,
        segments: List[Dict],
        speaker_map: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Map generic speaker labels (SPEAKER_00, SPEAKER_01) to therapy roles.

        Args:
            segments: Segments with "speaker" field
            speaker_map: Optional custom mapping, e.g., {"SPEAKER_00": "Therapist"}
                         If None, uses default mapping based on who speaks first

        Returns:
            Segments with mapped speaker labels
        """
        if speaker_map is None:
            # Default: Assume first speaker is therapist
            # (In practice, therapist usually starts session with greeting)
            speaker_map = {
                "SPEAKER_00": "Therapist",
                "SPEAKER_01": "Client",
                "UNKNOWN": "Unknown"
            }

        mapped = []
        for seg in segments:
            original_speaker = seg.get("speaker", "UNKNOWN")
            mapped_speaker = speaker_map.get(original_speaker, original_speaker)

            mapped.append({
                **seg,
                "speaker": mapped_speaker,
                "original_speaker": original_speaker  # Keep original for debugging
            })

        return mapped


class TranscriptionParser:
    """Parse and structure transcription data"""

    def parse(self, diarized_data: Dict) -> TranscriptionResult:
        """
        Parse diarized transcription into structured format
        - Group by speakers
        - Identify topics/sections
        - Extract key information
        """
        segments = []

        for seg in diarized_data.get("segments", []):
            segments.append(TranscriptionSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                speaker=seg.get("speaker"),
                confidence=seg.get("confidence")
            ))

        full_text = " ".join([s.text for s in segments])

        return TranscriptionResult(
            segments=segments,
            full_text=full_text,
            duration=diarized_data.get("duration", 0),
            language=diarized_data.get("language", "en"),
            metadata={
                "processed_at": datetime.now().isoformat(),
                "num_speakers": len(set(s.speaker for s in segments if s.speaker))
            }
        )

class UXFormatter:
    """Format transcription for user interface output"""

    def format_for_display(self, result: TranscriptionResult, format_type: str = "conversation") -> str:
        """
        Format transcription result for UI display
        Supports different format types:
        - conversation: Speaker-based dialogue format
        - timeline: Time-stamped format
        - paragraph: Continuous paragraph format
        """
        if format_type == "conversation":
            return self._format_conversation(result)
        elif format_type == "timeline":
            return self._format_timeline(result)
        elif format_type == "paragraph":
            return self._format_paragraph(result)
        else:
            return result.full_text

    def _format_conversation(self, result: TranscriptionResult) -> str:
        """Format as speaker-based conversation"""
        output = []
        current_speaker = None
        current_text = []

        for segment in result.segments:
            if segment.speaker != current_speaker:
                if current_text:
                    output.append(f"{current_speaker}: {' '.join(current_text)}")
                current_speaker = segment.speaker
                current_text = [segment.text]
            else:
                current_text.append(segment.text)

        if current_text:
            output.append(f"{current_speaker}: {' '.join(current_text)}")

        return "\n\n".join(output)

    def _format_timeline(self, result: TranscriptionResult) -> str:
        """Format with timestamps"""
        output = []
        for segment in result.segments:
            timestamp = f"[{self._format_time(segment.start)} - {self._format_time(segment.end)}]"
            speaker = f"{segment.speaker}: " if segment.speaker else ""
            output.append(f"{timestamp} {speaker}{segment.text}")

        return "\n".join(output)

    def _format_paragraph(self, result: TranscriptionResult) -> str:
        """Format as continuous paragraphs"""
        paragraphs = []
        current_para = []

        for segment in result.segments:
            current_para.append(segment.text)

            # Start new paragraph on speaker change or after certain length
            if len(" ".join(current_para)) > 500:
                paragraphs.append(" ".join(current_para))
                current_para = []

        if current_para:
            paragraphs.append(" ".join(current_para))

        return "\n\n".join(paragraphs)

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def format_therapy_session(self, result: TranscriptionResult) -> str:
        """
        Format specifically for therapy session review

        Features:
        - Header with session metadata
        - Timestamps every minute for easy navigation
        - Consecutive same-speaker segments merged into paragraphs
        - Clear therapist/client attribution
        - Ready for clinical review
        """
        output = []
        output.append("=" * 60)
        output.append("THERAPY SESSION TRANSCRIPT")
        output.append(f"Duration: {result.duration / 60:.1f} minutes")
        output.append(f"Processed: {result.metadata.get('processed_at', 'N/A')}")

        # Show number of speakers detected
        num_speakers = result.metadata.get('num_speakers', 0)
        output.append(f"Speakers: {num_speakers}")

        output.append("=" * 60)
        output.append("")

        # Merge consecutive segments from same speaker for readability
        merged_segments = self._merge_consecutive_speaker_segments(result.segments)

        current_minute = -1

        for seg in merged_segments:
            minute = int(seg.start // 60)

            # Add timestamp marker every minute
            if minute > current_minute:
                output.append("")
                output.append(f"--- [{minute}:00] ---")
                output.append("")
                current_minute = minute

            # Format: [start-end] Speaker: text
            timestamp = f"[{self._format_time(seg.start)} - {self._format_time(seg.end)}]"
            speaker = seg.speaker if seg.speaker else "Unknown"

            output.append(f"{timestamp} {speaker}:")
            output.append(seg.text)
            output.append("")

        output.append("=" * 60)
        output.append("END OF TRANSCRIPT")
        output.append("=" * 60)

        return "\n".join(output)

    def _merge_consecutive_speaker_segments(
        self,
        segments: List[TranscriptionSegment]
    ) -> List[TranscriptionSegment]:
        """
        Merge consecutive segments from the same speaker into single blocks.

        This improves readability - instead of:
            [0:00-0:05] Therapist: Hello
            [0:05-0:08] Therapist: How are you?

        We get:
            [0:00-0:08] Therapist: Hello How are you?
        """
        if not segments:
            return []

        merged = []
        current = None

        for seg in segments:
            if current is None:
                # First segment
                current = TranscriptionSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    speaker=seg.speaker,
                    confidence=seg.confidence
                )
            elif seg.speaker == current.speaker:
                # Same speaker - merge
                current.end = seg.end
                current.text += " " + seg.text
            else:
                # Speaker changed - save current and start new
                merged.append(current)
                current = TranscriptionSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    speaker=seg.speaker,
                    confidence=seg.confidence
                )

        # Don't forget the last segment
        if current:
            merged.append(current)

        return merged

class AudioTranscriptionPipeline:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        self.transcriber = WhisperTranscriber()
        self.postprocessor = PostProcessor()
        self._diarizer = None  # Lazy initialization - model is heavy (~1GB)
        self.parser = TranscriptionParser()
        self.formatter = UXFormatter()

    @property
    def diarizer(self):
        """Lazy-load diarizer only when needed (avoids loading 1GB model on startup)"""
        if self._diarizer is None:
            print("[Pipeline] Initializing speaker diarizer (first time only)...")
            self._diarizer = SpeakerDiarizer()
        return self._diarizer

    def process(self,
                audio_path: str,
                output_format: str = "conversation",
                enable_diarization: bool = True) -> Tuple[TranscriptionResult, str]:
        """
        Run complete audio transcription pipeline

        Args:
            audio_path: Path to audio file
            output_format: Output format type (conversation, timeline, paragraph)
            enable_diarization: Whether to perform speaker diarization

        Returns:
            Tuple of (TranscriptionResult, formatted_output)
        """
        print(f"\n{'='*50}")
        print(f"Starting Audio Transcription Pipeline")
        print(f"{'='*50}\n")

        # Step 1: Preprocess audio
        print("Step 1: Preprocessing audio...")
        processed_audio = self.preprocessor.preprocess(audio_path)

        # Step 2: Transcribe with Whisper
        print("Step 2: Transcribing with Whisper...")
        transcription = self.transcriber.transcribe(processed_audio)

        # Step 3: Post-process text
        print("Step 3: Post-processing text...")
        cleaned = self.postprocessor.process(transcription)

        # Step 4: Speaker diarization (optional)
        if enable_diarization:
            print("Step 4: Performing speaker diarization...")
            diarized = self.diarizer.diarize(processed_audio, cleaned)

            # Map to therapy-friendly labels (Therapist/Client)
            print("[Pipeline] Mapping speakers to therapy roles...")
            diarized["segments"] = self.diarizer.map_therapy_speakers(
                diarized["segments"]
            )
        else:
            print("Step 4: Skipping diarization")
            diarized = cleaned

        # Step 5: Parse and structure
        print("Step 5: Parsing and structuring...")
        result = self.parser.parse(diarized)

        # Step 6: Format for output
        print("Step 6: Formatting for display...")
        formatted = self.formatter.format_for_display(result, output_format)

        print(f"\n{'='*50}")
        print(f"Pipeline Complete!")
        print(f"Duration: {result.duration:.1f} seconds")
        print(f"Segments: {len(result.segments)}")
        print(f"Speakers: {result.metadata.get('num_speakers', 1)}")
        print(f"{'='*50}\n")

        return result, formatted

    def process_long_audio(self,
                           audio_path: str,
                           output_format: str = "therapy",
                           enable_diarization: bool = False,
                           cleanup_chunks: bool = True) -> Tuple[TranscriptionResult, str]:
        """
        Process long audio files (up to ~2 hours) that exceed Whisper's 25MB limit.

        Automatically detects if chunking is needed based on estimated output size.
        Uses silence detection to split at natural conversation pauses.

        Args:
            audio_path: Path to audio file (any duration)
            output_format: Output format type ("therapy", "conversation", "timeline", "paragraph")
            enable_diarization: Whether to perform speaker diarization
            cleanup_chunks: Whether to delete temporary chunk files after processing

        Returns:
            Tuple of (TranscriptionResult, formatted_output)
        """
        print(f"\n{'='*60}")
        print(f"Starting Long Audio Transcription Pipeline")
        print(f"{'='*60}\n")

        # Step 1: Validate and check if chunking is needed
        print("Step 1: Analyzing audio file...")
        info = self.preprocessor.validate_audio(audio_path)
        if not info["valid"]:
            raise ValueError(f"Invalid audio file: {info.get('error')}")

        duration_min = info["duration_seconds"] / 60
        print(f"[Pipeline] Duration: {duration_min:.1f} minutes")

        # Estimate processed file size (0.46 MB/min at 64kbps mono)
        estimated_size_mb = duration_min * 0.46
        print(f"[Pipeline] Estimated processed size: {estimated_size_mb:.1f} MB")

        needs_chunking = estimated_size_mb > 20  # Use 20MB threshold for safety margin

        if needs_chunking:
            print(f"[Pipeline] File exceeds 20MB limit - will split into chunks")
            # Step 2a: Preprocess with chunking
            print("\nStep 2: Preprocessing and chunking audio...")
            chunks = self.preprocessor.preprocess_long_audio(audio_path)

            # Step 3a: Transcribe all chunks
            print("\nStep 3: Transcribing chunks...")
            transcription = self.transcriber.transcribe_chunks(chunks)

            # Cleanup temporary chunk files
            if cleanup_chunks:
                print("\n[Pipeline] Cleaning up temporary chunk files...")
                for chunk_path, _ in chunks:
                    try:
                        os.remove(chunk_path)
                    except OSError:
                        pass
        else:
            print(f"[Pipeline] File under 20MB limit - processing directly")
            # Step 2b: Standard preprocessing
            print("\nStep 2: Preprocessing audio...")
            processed_audio = self.preprocessor.preprocess(audio_path)

            # Step 3b: Standard transcription
            print("\nStep 3: Transcribing with Whisper...")
            transcription = self.transcriber.transcribe(processed_audio)

        # Step 4: Post-process text
        print("\nStep 4: Post-processing text...")
        cleaned = self.postprocessor.process(transcription)

        # Step 5: Speaker diarization (optional)
        if enable_diarization:
            print("\nStep 5: Performing speaker diarization...")
            diarized = self.diarizer.diarize(audio_path, cleaned)

            # Map to therapy-friendly labels (Therapist/Client)
            print("[Pipeline] Mapping speakers to therapy roles...")
            diarized["segments"] = self.diarizer.map_therapy_speakers(
                diarized["segments"]
            )
        else:
            print("\nStep 5: Skipping diarization")
            diarized = cleaned

        # Step 6: Parse and structure
        print("\nStep 6: Parsing and structuring...")
        result = self.parser.parse(diarized)

        # Step 7: Format for output
        print("\nStep 7: Formatting for display...")
        if output_format == "therapy":
            formatted = self.formatter.format_therapy_session(result)
        else:
            formatted = self.formatter.format_for_display(result, output_format)

        print(f"\n{'='*60}")
        print(f"Long Audio Pipeline Complete!")
        print(f"Duration: {result.duration:.1f} seconds ({result.duration/60:.1f} minutes)")
        print(f"Segments: {len(result.segments)}")
        if needs_chunking:
            print(f"Chunks processed: {len(chunks)}")
        print(f"{'='*60}\n")

        return result, formatted

def main():
    """Example usage of the pipeline"""

    # Initialize pipeline
    pipeline = AudioTranscriptionPipeline()

    # Example: Process an audio file
    audio_file = "test-audio.mp3"

    if os.path.exists(audio_file):
        result, formatted_output = pipeline.process(
            audio_file,
            output_format="conversation",
            enable_diarization=True
        )

        print("Formatted Output:")
        print("-" * 40)
        print(formatted_output)
        print("-" * 40)

        # Save results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        # Save formatted text
        with open(output_dir / "transcription.txt", "w") as f:
            f.write(formatted_output)

        # Save structured data
        with open(output_dir / "transcription.json", "w") as f:
            json.dump({
                "segments": [
                    {
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                        "speaker": s.speaker,
                        "confidence": s.confidence
                    }
                    for s in result.segments
                ],
                "metadata": result.metadata
            }, f, indent=2)

        print(f"\nResults saved to {output_dir}/")
    else:
        print(f"Audio file not found: {audio_file}")
        print("Please provide an audio file to process.")

if __name__ == "__main__":
    main()