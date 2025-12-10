#!/usr/bin/env python3
"""
Verification Script - Python 3.13 + pydub Compatibility
========================================================

This script verifies that your Python 3.13 environment is correctly
set up with all dependencies working properly.
"""

import sys
import os

def verify_python_version():
    """Verify Python version is 3.13+"""
    print(f"Python Version: {sys.version}")
    if sys.version_info >= (3, 13):
        print("✅ Python 3.13+ detected")
        return True
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected (need 3.13+)")
        return False

def verify_pydub():
    """Verify pydub imports and basic functionality"""
    try:
        from pydub import AudioSegment
        from pydub import effects
        print("✅ pydub imports successfully")

        # Check if audioop-lts is being used
        import audioop
        print("✅ audioop-lts is providing compatibility layer")
        return True
    except ImportError as e:
        print(f"❌ pydub import failed: {e}")
        return False

def verify_openai():
    """Verify OpenAI client imports"""
    try:
        from openai import OpenAI
        print("✅ OpenAI client imports successfully")
        return True
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False

def verify_pipeline():
    """Verify pipeline imports and initializes"""
    try:
        # Add parent directory to path to import from src
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.pipeline import AudioTranscriptionPipeline, AudioPreprocessor, WhisperTranscriber
        print("✅ Pipeline modules import successfully")

        # Try to instantiate (will fail if API key missing, but that's okay)
        preprocessor = AudioPreprocessor()
        print("✅ AudioPreprocessor initializes successfully")

        return True
    except Exception as e:
        print(f"❌ Pipeline verification failed: {e}")
        return False

def verify_ffmpeg():
    """Verify ffmpeg is installed"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ ffmpeg installed: {version_line}")
            return True
        else:
            print("❌ ffmpeg not responding correctly")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found - install with: brew install ffmpeg")
        return False
    except Exception as e:
        print(f"⚠️  ffmpeg check failed: {e}")
        return False

def main():
    print("="*60)
    print("Python 3.13 + pydub Compatibility Verification")
    print("="*60)
    print()

    checks = [
        ("Python Version", verify_python_version),
        ("pydub + audioop-lts", verify_pydub),
        ("OpenAI Client", verify_openai),
        ("Pipeline Components", verify_pipeline),
        ("ffmpeg", verify_ffmpeg),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        results.append(check_func())
        print()

    print("="*60)
    if all(results):
        print("✅ ALL CHECKS PASSED - System is ready!")
    else:
        print("⚠️  Some checks failed - see above for details")
    print("="*60)

if __name__ == "__main__":
    main()
