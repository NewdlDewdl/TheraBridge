"""
Audio transcription service - wrapper for existing pipeline
"""
import sys
from pathlib import Path
from typing import Dict

# Add audio-transcription-pipeline to path
PIPELINE_DIR = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from src.pipeline import AudioTranscriptionPipeline


async def transcribe_audio_file(audio_path: str) -> Dict:
    """
    Transcribe audio file using the existing pipeline

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with segments, full_text, language, duration
    """
    pipeline = AudioTranscriptionPipeline()
    result = pipeline.process(audio_path)
    return result
