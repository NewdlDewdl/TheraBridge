#!/usr/bin/env python3
"""
Audio Transcription Pipeline
============================

Simplified pipeline for audio processing:
1. Audio preprocessing (format conversion, normalization)
2. Whisper transcription (OpenAI API)
"""

import os
from pathlib import Path
from typing import Dict, Optional

class AudioPreprocessor:
    """Handles audio preprocessing before transcription"""

    def __init__(self,
                 target_format: str = "mp3",
                 target_sample_rate: int = 16000,
                 target_bitrate: str = "64k",
                 max_file_size_mb: int = 25):
        self.target_format = target_format
        self.target_sample_rate = target_sample_rate
        self.target_bitrate = target_bitrate
        self.max_file_size_mb = max_file_size_mb

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


class AudioTranscriptionPipeline:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        self.transcriber = WhisperTranscriber()

    def process(self, audio_path: str) -> Dict:
        """
        Run complete audio transcription pipeline

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with transcription data (segments, full_text, language, duration)
        """
        print(f"\n{'='*50}")
        print(f"Starting Audio Transcription Pipeline")
        print(f"{'='*50}\n")

        # Step 1: Preprocess audio
        print("Step 1: Preprocessing audio...")
        processed_audio = self.preprocessor.preprocess(audio_path)

        # Step 2: Transcribe with Whisper
        print("\nStep 2: Transcribing with Whisper...")
        transcription = self.transcriber.transcribe(processed_audio)

        print(f"\n{'='*50}")
        print(f"Pipeline Complete!")
        print(f"Duration: {transcription.get('duration', 'N/A')} seconds")
        print(f"Segments: {len(transcription['segments'])}")
        print(f"{'='*50}\n")

        return transcription


def main():
    """Example usage of the pipeline"""
    import json

    # Initialize pipeline
    pipeline = AudioTranscriptionPipeline()

    # Example: Process an audio file
    audio_file = "test-audio.mp3"

    if os.path.exists(audio_file):
        result = pipeline.process(audio_file)

        print("Transcription Result:")
        print("-" * 40)
        print(f"Language: {result['language']}")
        print(f"Duration: {result.get('duration', 'N/A')}s")
        print(f"\nFull Text:\n{result['full_text']}")
        print("-" * 40)

        # Save results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        # Save full text
        with open(output_dir / "transcription.txt", "w") as f:
            f.write(result['full_text'])

        # Save structured data
        with open(output_dir / "transcription.json", "w") as f:
            json.dump(result, f, indent=2)

        print(f"\nResults saved to {output_dir}/")
    else:
        print(f"Audio file not found: {audio_file}")
        print("Please provide an audio file to process.")


if __name__ == "__main__":
    main()
