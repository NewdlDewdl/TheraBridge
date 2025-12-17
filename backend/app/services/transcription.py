"""
Audio transcription service - wrapper for existing pipeline
"""
import os
import sys
from pathlib import Path
from typing import Dict


def get_pipeline_directory() -> Path:
    """
    Resolve the audio transcription pipeline directory with validation.

    Checks in order:
    1. AUDIO_PIPELINE_DIR environment variable (absolute path)
    2. Default monorepo location (../audio-transcription-pipeline)

    Returns:
        Path: Validated pipeline directory

    Raises:
        RuntimeError: If pipeline directory cannot be found or is invalid
    """
    # Try environment variable first (production/deployment use case)
    env_path = os.getenv("AUDIO_PIPELINE_DIR")
    if env_path:
        pipeline_dir = Path(env_path).resolve()
        if pipeline_dir.is_dir() and (pipeline_dir / "src" / "pipeline.py").exists():
            return pipeline_dir
        raise RuntimeError(
            f"AUDIO_PIPELINE_DIR set to '{env_path}' but directory is invalid. "
            f"Expected 'src/pipeline.py' to exist."
        )

    # Fall back to monorepo structure (development use case)
    backend_root = Path(__file__).parent.parent.parent
    pipeline_dir = (backend_root.parent / "audio-transcription-pipeline").resolve()

    if pipeline_dir.is_dir() and (pipeline_dir / "src" / "pipeline.py").exists():
        return pipeline_dir

    raise RuntimeError(
        f"Audio transcription pipeline not found. Tried:\n"
        f"  1. Environment variable AUDIO_PIPELINE_DIR (not set)\n"
        f"  2. Monorepo location: {pipeline_dir} (not found)\n"
        f"Please set AUDIO_PIPELINE_DIR or ensure monorepo structure is intact."
    )


# Initialize and validate pipeline directory
PIPELINE_DIR = get_pipeline_directory()
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
