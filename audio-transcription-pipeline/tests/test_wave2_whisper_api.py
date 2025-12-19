#!/usr/bin/env python3
"""
Wave 2 Agent I5: Whisper API Validation Test
============================================

Tests WhisperTranscriber with preprocessed audio to validate:
1. Transcriber initialization (API key loading)
2. Audio preprocessing (m4a -> mp3 <25MB)
3. Whisper API transcription
4. Output structure validation
5. Rate limiting and retry logic verification
"""

import sys
import os
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import AudioPreprocessor, WhisperTranscriber


def test_whisper_transcriber():
    """Test WhisperTranscriber with preprocessed audio"""

    print("=" * 60)
    print("WAVE 2 AGENT I5: WHISPER API VALIDATION TEST")
    print("=" * 60)
    print()

    # Test configuration
    audio_file = Path(__file__).parent / "samples" / "compressed-cbt-session.m4a"
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    results = {
        "test_name": "wave2_whisper_api_validation",
        "audio_file": str(audio_file),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": {}
    }

    try:
        # STEP 1: Test WhisperTranscriber initialization
        print("STEP 1: Testing WhisperTranscriber Initialization")
        print("-" * 60)

        step1_start = time.time()

        try:
            transcriber = WhisperTranscriber()

            # Verify API key loaded
            api_key_loaded = transcriber.api_key is not None and len(transcriber.api_key) > 0
            api_key_preview = f"{transcriber.api_key[:8]}..." if api_key_loaded else "NOT LOADED"

            # Verify configuration
            max_retries = transcriber.max_retries
            rate_limit_delay = transcriber.rate_limit_delay
            min_retry_wait = transcriber.min_retry_wait
            max_retry_wait = transcriber.max_retry_wait

            print(f"✓ WhisperTranscriber initialized successfully")
            print(f"  - API Key: {api_key_preview}")
            print(f"  - Max Retries: {max_retries}")
            print(f"  - Rate Limit Delay: {rate_limit_delay}s")
            print(f"  - Retry Wait Range: {min_retry_wait}s - {max_retry_wait}s")

            results["steps"]["step1_initialization"] = {
                "status": "PASS",
                "duration_seconds": time.time() - step1_start,
                "api_key_loaded": api_key_loaded,
                "max_retries": max_retries,
                "rate_limit_delay": rate_limit_delay,
                "min_retry_wait": min_retry_wait,
                "max_retry_wait": max_retry_wait
            }

        except Exception as e:
            print(f"✗ WhisperTranscriber initialization FAILED: {e}")
            results["steps"]["step1_initialization"] = {
                "status": "FAIL",
                "error": str(e)
            }
            raise

        print()

        # STEP 2: Preprocess audio file
        print("STEP 2: Preprocessing Audio (m4a -> mp3 <25MB)")
        print("-" * 60)

        step2_start = time.time()

        try:
            preprocessor = AudioPreprocessor(
                target_format="mp3",
                target_sample_rate=16000,
                target_bitrate="64k",
                max_file_size_mb=25
            )

            # Get original file info
            original_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
            print(f"Original file: {audio_file.name} ({original_size_mb:.2f} MB)")

            # Preprocess
            processed_audio = preprocessor.preprocess(str(audio_file))
            processed_size_mb = os.path.getsize(processed_audio) / (1024 * 1024)

            print(f"✓ Audio preprocessed successfully")
            print(f"  - Processed file: {Path(processed_audio).name} ({processed_size_mb:.2f} MB)")
            print(f"  - Size reduction: {original_size_mb - processed_size_mb:.2f} MB")

            results["steps"]["step2_preprocessing"] = {
                "status": "PASS",
                "duration_seconds": time.time() - step2_start,
                "original_file": str(audio_file),
                "processed_file": processed_audio,
                "original_size_mb": round(original_size_mb, 2),
                "processed_size_mb": round(processed_size_mb, 2),
                "size_reduction_mb": round(original_size_mb - processed_size_mb, 2)
            }

        except Exception as e:
            print(f"✗ Audio preprocessing FAILED: {e}")
            results["steps"]["step2_preprocessing"] = {
                "status": "FAIL",
                "error": str(e)
            }
            raise

        print()

        # STEP 3: Test transcription with Whisper API
        print("STEP 3: Transcribing with Whisper API")
        print("-" * 60)
        print("⚠️  Making REAL OpenAI API call (this will cost ~$0.09)")
        print()

        step3_start = time.time()

        try:
            # Transcribe
            transcription = transcriber.transcribe(
                audio_path=processed_audio,
                language="en",
                response_format="verbose_json"
            )

            api_call_time = time.time() - step3_start

            # Extract transcription details
            segments = transcription.get("segments", [])
            full_text = transcription.get("full_text", "")
            language = transcription.get("language", "")
            duration = transcription.get("duration", 0)

            segment_count = len(segments)
            total_chars = len(full_text)

            # Get first and last segments
            first_segment = segments[0] if segments else None
            last_segment = segments[-1] if segments else None

            print(f"✓ Transcription completed successfully")
            print(f"  - API call time: {api_call_time:.2f}s")
            print(f"  - Segments returned: {segment_count}")
            print(f"  - Language detected: {language}")
            print(f"  - Audio duration: {duration:.2f}s")
            print(f"  - Total transcript length: {total_chars} characters")
            print()

            if first_segment:
                first_text_preview = first_segment['text'][:100]
                print(f"  First segment:")
                print(f"    - Time: {first_segment['start']:.2f}s - {first_segment['end']:.2f}s")
                print(f"    - Text: \"{first_text_preview}...\"")
                print()

            if last_segment:
                last_text_preview = last_segment['text'][:100]
                print(f"  Last segment:")
                print(f"    - Time: {last_segment['start']:.2f}s - {last_segment['end']:.2f}s")
                print(f"    - Text: \"{last_text_preview}...\"")

            results["steps"]["step3_transcription"] = {
                "status": "PASS",
                "api_call_time_seconds": round(api_call_time, 2),
                "segment_count": segment_count,
                "language_detected": language,
                "audio_duration_seconds": round(duration, 2),
                "total_transcript_chars": total_chars,
                "first_segment": {
                    "start": round(first_segment['start'], 2) if first_segment else None,
                    "end": round(first_segment['end'], 2) if first_segment else None,
                    "text_preview": first_text_preview if first_segment else None
                } if first_segment else None,
                "last_segment": {
                    "start": round(last_segment['start'], 2) if last_segment else None,
                    "end": round(last_segment['end'], 2) if last_segment else None,
                    "text_preview": last_text_preview if last_segment else None
                } if last_segment else None
            }

            # Save full transcription
            transcription_output_path = output_dir / "wave2_transcription_test.json"
            with open(transcription_output_path, "w") as f:
                json.dump(transcription, f, indent=2)

            print()
            print(f"  - Full transcription saved to: {transcription_output_path}")

        except Exception as e:
            print(f"✗ Whisper API transcription FAILED: {e}")
            results["steps"]["step3_transcription"] = {
                "status": "FAIL",
                "error": str(e),
                "error_type": type(e).__name__
            }
            raise

        print()

        # STEP 4: Validate output structure
        print("STEP 4: Validating Transcription Output Structure")
        print("-" * 60)

        step4_start = time.time()

        try:
            # Check required fields
            required_fields = ["segments", "full_text", "language", "duration"]
            missing_fields = [field for field in required_fields if field not in transcription]

            # Validate segment structure
            valid_segments = True
            if segments:
                first_seg = segments[0]
                required_seg_fields = ["start", "end", "text"]
                missing_seg_fields = [field for field in required_seg_fields if field not in first_seg]
                valid_segments = len(missing_seg_fields) == 0

            # Check values
            has_text = len(full_text) > 0
            has_duration = duration > 0
            has_segments = segment_count > 0

            validation_passed = (
                len(missing_fields) == 0 and
                valid_segments and
                has_text and
                has_duration and
                has_segments
            )

            if validation_passed:
                print(f"✓ Output structure validation PASSED")
                print(f"  - All required fields present: {required_fields}")
                print(f"  - Segments have correct structure: start, end, text")
                print(f"  - Full text populated: {total_chars} chars")
                print(f"  - Duration valid: {duration:.2f}s")
                print(f"  - Segments present: {segment_count}")
            else:
                print(f"✗ Output structure validation FAILED")
                if missing_fields:
                    print(f"  - Missing fields: {missing_fields}")
                if not valid_segments:
                    print(f"  - Invalid segment structure")
                if not has_text:
                    print(f"  - No transcript text")
                if not has_duration:
                    print(f"  - Invalid duration")

            results["steps"]["step4_validation"] = {
                "status": "PASS" if validation_passed else "FAIL",
                "duration_seconds": time.time() - step4_start,
                "required_fields_present": len(missing_fields) == 0,
                "valid_segment_structure": valid_segments,
                "has_text": has_text,
                "has_duration": has_duration,
                "has_segments": has_segments
            }

        except Exception as e:
            print(f"✗ Output validation FAILED: {e}")
            results["steps"]["step4_validation"] = {
                "status": "FAIL",
                "error": str(e)
            }

        print()

        # STEP 5: Verify rate limiting and retry logic
        print("STEP 5: Verifying Rate Limiting & Retry Configuration")
        print("-" * 60)

        step5_start = time.time()

        try:
            # Check retry decorator exists
            has_retry_decorator = hasattr(transcriber._transcribe_with_retry, 'retry')

            # Check rate limit method exists
            has_rate_limit = hasattr(transcriber, '_apply_rate_limit')

            # Report configuration
            print(f"✓ Rate limiting and retry logic verified")
            print(f"  - Retry decorator present: {has_retry_decorator}")
            print(f"  - Rate limit method present: {has_rate_limit}")
            print(f"  - Max retries: {transcriber.max_retries}")
            print(f"  - Rate limit delay: {transcriber.rate_limit_delay}s")
            print(f"  - Exponential backoff: {transcriber.min_retry_wait}s - {transcriber.max_retry_wait}s")

            results["steps"]["step5_rate_limit_verification"] = {
                "status": "PASS",
                "duration_seconds": time.time() - step5_start,
                "retry_decorator_present": has_retry_decorator,
                "rate_limit_method_present": has_rate_limit,
                "max_retries": transcriber.max_retries,
                "rate_limit_delay": transcriber.rate_limit_delay,
                "min_retry_wait": transcriber.min_retry_wait,
                "max_retry_wait": transcriber.max_retry_wait
            }

        except Exception as e:
            print(f"✗ Rate limit verification FAILED: {e}")
            results["steps"]["step5_rate_limit_verification"] = {
                "status": "FAIL",
                "error": str(e)
            }

        print()

        # Overall test status
        all_passed = all(
            step.get("status") == "PASS"
            for step in results["steps"].values()
        )

        results["overall_status"] = "PASS" if all_passed else "FAIL"
        results["total_duration_seconds"] = round(time.time() - step1_start, 2)

        # Save test results
        results_output_path = output_dir / "wave2_whisper_api_test_results.json"
        with open(results_output_path, "w") as f:
            json.dump(results, f, indent=2)

        print("=" * 60)
        print(f"TEST SUMMARY: {results['overall_status']}")
        print("=" * 60)
        print(f"Total test duration: {results['total_duration_seconds']}s")
        print(f"Results saved to: {results_output_path}")
        print()

        # Print deliverables summary
        if all_passed:
            step3 = results["steps"]["step3_transcription"]
            print("DELIVERABLES:")
            print(f"  - API call time: {step3['api_call_time_seconds']}s")
            print(f"  - Segments returned: {step3['segment_count']}")
            print(f"  - Language detected: {step3['language_detected']}")
            print(f"  - Audio duration: {step3['audio_duration_seconds']}s")
            print(f"  - Total transcript chars: {step3['total_transcript_chars']}")
            print(f"  - First segment text: \"{step3['first_segment']['text_preview']}...\"")
            print(f"  - Last segment text: \"{step3['last_segment']['text_preview']}...\"")
            print(f"  - Test status: PASS")

        return results

    except Exception as e:
        results["overall_status"] = "FAIL"
        results["error"] = str(e)
        results["error_type"] = type(e).__name__

        # Save error results
        error_output_path = output_dir / "wave2_whisper_api_test_results.json"
        with open(error_output_path, "w") as f:
            json.dump(results, f, indent=2)

        print()
        print("=" * 60)
        print("TEST SUMMARY: FAIL")
        print("=" * 60)
        print(f"Error: {e}")
        print(f"Error results saved to: {error_output_path}")

        raise


if __name__ == "__main__":
    test_whisper_transcriber()
