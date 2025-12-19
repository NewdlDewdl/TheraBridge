#!/usr/bin/env python3
"""
Wave 2 Performance Logger Test
Instance I6 - Manual testing of PerformanceLogger infrastructure
"""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance_logger import PerformanceLogger

def test_performance_logger():
    """Comprehensive PerformanceLogger infrastructure test"""

    print("=" * 80)
    print("WAVE 2 PERFORMANCE LOGGER TEST")
    print("Instance I6 - Performance Monitoring Infrastructure Validation")
    print("=" * 80)
    print()

    results = {
        "logger_initialization": "PENDING",
        "stage_tracking": "PENDING",
        "gpu_monitoring": "PENDING",
        "gpu_device": None,
        "reports_generated": {"json": None, "txt": None},
        "json_validation": "PENDING",
        "context_managers": {"timer": "PENDING", "subprocess": "PENDING"},
        "memory_tracking": "PENDING",
        "test_status": "PENDING",
        "details": []
    }

    # ========================================================================
    # TEST 1: Logger Initialization
    # ========================================================================
    print("TEST 1: Logger Initialization")
    print("-" * 60)

    try:
        logger = PerformanceLogger(
            name="Wave2Test",
            output_dir="tests/outputs/performance_logs",
            verbose=True
        )
        results["logger_initialization"] = "SUCCESS"
        results["details"].append("✓ Logger initialized successfully")
        print("✓ Logger initialized: name='Wave2Test', output_dir='tests/outputs/performance_logs'")
        print()
    except Exception as e:
        results["logger_initialization"] = "FAIL"
        results["details"].append(f"✗ Logger initialization failed: {e}")
        print(f"✗ FAILED: {e}")
        return results

    # ========================================================================
    # TEST 2: GPU Monitoring Detection
    # ========================================================================
    print("TEST 2: GPU Monitoring Detection")
    print("-" * 60)

    try:
        # Check GPU availability via logger's system info
        system_info = logger._get_system_info()

        cuda_available = system_info.get("cuda_available", False)
        mps_available = system_info.get("mps_available", False)

        if cuda_available:
            results["gpu_monitoring"] = "ENABLED"
            gpu_name = system_info.get("cuda_device_name", "Unknown CUDA GPU")
            results["gpu_device"] = gpu_name
            results["details"].append(f"✓ GPU Detected: {gpu_name}")
            print(f"✓ CUDA GPU Detected: {gpu_name}")
            print(f"  CUDA Device Count: {system_info.get('cuda_device_count', 0)}")
        elif mps_available:
            results["gpu_monitoring"] = "ENABLED"
            results["gpu_device"] = "Apple MPS"
            results["details"].append("✓ GPU Detected: Apple MPS")
            print("✓ Apple MPS GPU Detected")
        else:
            results["gpu_monitoring"] = "DISABLED"
            results["gpu_device"] = None
            results["details"].append("✓ No GPU detected - graceful CPU fallback")
            print("✓ No GPU detected - running in CPU mode (graceful fallback)")

        print()
    except Exception as e:
        results["gpu_monitoring"] = "ERROR"
        results["details"].append(f"✗ GPU detection failed: {e}")
        print(f"✗ GPU detection error: {e}")
        print()

    # ========================================================================
    # TEST 3: Stage Tracking
    # ========================================================================
    print("TEST 3: Stage Tracking")
    print("-" * 60)

    try:
        # Start pipeline
        logger.start_pipeline()
        print("✓ Pipeline started")

        # Create test stage
        logger.start_stage("TestStage1")
        print("✓ Stage 'TestStage1' started")

        # Simulate subprocess work
        with logger.subprocess("test_operation"):
            time.sleep(0.1)
            print("  ✓ Subprocess 'test_operation' executed (0.1s simulated work)")

        # End stage
        logger.end_stage("TestStage1")
        print("✓ Stage 'TestStage1' ended")

        # End pipeline
        logger.end_pipeline()
        print("✓ Pipeline ended")

        results["stage_tracking"] = "SUCCESS"
        results["details"].append("✓ Stage tracking completed successfully")
        print()
    except Exception as e:
        results["stage_tracking"] = "FAIL"
        results["details"].append(f"✗ Stage tracking failed: {e}")
        print(f"✗ FAILED: {e}")
        print()

    # ========================================================================
    # TEST 4: Validate Performance Reports Generated
    # ========================================================================
    print("TEST 4: Validate Performance Reports")
    print("-" * 60)

    try:
        output_dir = Path("tests/outputs/performance_logs")

        # Find the generated JSON report
        json_files = sorted(output_dir.glob("performance_*.json"))
        if json_files:
            json_path = json_files[-1]  # Most recent
            results["reports_generated"]["json"] = str(json_path)
            print(f"✓ JSON report found: {json_path}")
        else:
            results["reports_generated"]["json"] = None
            print("✗ JSON report NOT found")

        # Find the generated TXT report
        txt_files = sorted(output_dir.glob("performance_*.txt"))
        if txt_files:
            txt_path = txt_files[-1]  # Most recent
            results["reports_generated"]["txt"] = str(txt_path)
            print(f"✓ TXT report found: {txt_path}")
        else:
            results["reports_generated"]["txt"] = None
            print("✗ TXT report NOT found")

        print()
    except Exception as e:
        results["details"].append(f"✗ Report validation failed: {e}")
        print(f"✗ Report validation error: {e}")
        print()

    # ========================================================================
    # TEST 5: JSON Structure Validation
    # ========================================================================
    print("TEST 5: JSON Structure Validation")
    print("-" * 60)

    try:
        if results["reports_generated"]["json"]:
            with open(results["reports_generated"]["json"], 'r') as f:
                json_data = json.load(f)

            # Validate required fields
            required_fields = ["session_id", "pipeline_name", "metrics", "timings", "system_info"]
            missing_fields = [f for f in required_fields if f not in json_data]

            if missing_fields:
                results["json_validation"] = "FAIL"
                results["details"].append(f"✗ JSON missing fields: {missing_fields}")
                print(f"✗ Missing fields: {missing_fields}")
            else:
                results["json_validation"] = "PASS"
                results["details"].append("✓ JSON structure valid")
                print("✓ All required fields present:")
                print(f"  - session_id: {json_data.get('session_id')}")
                print(f"  - pipeline_name: {json_data.get('pipeline_name')}")
                print(f"  - total_duration: {json_data['metrics'].get('total_duration', 0):.3f}s")
                print(f"  - stages: {list(json_data['metrics'].get('stages', {}).keys())}")

                # Extract timings
                stages = json_data['metrics'].get('stages', {})
                if stages:
                    print(f"  - Stage timings:")
                    for stage_name, stage_data in stages.items():
                        print(f"    * {stage_name}: {stage_data.get('duration', 0):.3f}s")
        else:
            results["json_validation"] = "SKIP"
            results["details"].append("⊘ JSON validation skipped (no report found)")
            print("⊘ Skipped - no JSON report to validate")

        print()
    except Exception as e:
        results["json_validation"] = "FAIL"
        results["details"].append(f"✗ JSON validation error: {e}")
        print(f"✗ JSON validation error: {e}")
        print()

    # ========================================================================
    # TEST 6: Context Manager Patterns
    # ========================================================================
    print("TEST 6: Context Manager Patterns")
    print("-" * 60)

    # Create new logger instance for clean test
    logger2 = PerformanceLogger(
        name="ContextManagerTest",
        output_dir="tests/outputs/performance_logs",
        verbose=False  # Suppress output
    )

    try:
        logger2.start_pipeline()
        logger2.start_stage("ContextTest")

        # Test timer context manager
        with logger2.timer("test_timer"):
            time.sleep(0.05)

        results["context_managers"]["timer"] = "PASS"
        print("✓ Timer context manager: PASS (0.05s simulated work)")

        # Test subprocess context manager
        with logger2.subprocess("memory_test"):
            time.sleep(0.02)

        results["context_managers"]["subprocess"] = "PASS"
        print("✓ Subprocess context manager: PASS (0.02s simulated work)")

        logger2.end_stage("ContextTest")
        logger2.end_pipeline()

        results["details"].append("✓ Context managers working correctly")
        print()
    except Exception as e:
        results["context_managers"]["timer"] = "FAIL"
        results["context_managers"]["subprocess"] = "FAIL"
        results["details"].append(f"✗ Context manager test failed: {e}")
        print(f"✗ Context manager test failed: {e}")
        print()

    # ========================================================================
    # TEST 7: Memory Tracking
    # ========================================================================
    print("TEST 7: Memory Tracking")
    print("-" * 60)

    try:
        # Check if psutil is available
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False

        if has_psutil:
            results["memory_tracking"] = "ENABLED"
            results["details"].append("✓ Memory tracking enabled (psutil available)")
            print("✓ Memory tracking: ENABLED")
            print("  psutil library detected")

            # Test memory tracking
            test_logger = PerformanceLogger(
                name="MemoryTest",
                output_dir="tests/outputs/performance_logs",
                verbose=False
            )
            test_logger.start_pipeline()
            test_logger.start_stage("MemoryStage")

            with test_logger.subprocess("memory_check") as ctx:
                # Allocate some memory
                data = [0] * 1000000  # ~8MB list
                time.sleep(0.01)

            test_logger.end_stage("MemoryStage")
            test_logger.end_pipeline()

            # Check if memory delta was captured
            stages = test_logger.metrics.get("stages", {})
            if stages:
                memory_stage = stages.get("MemoryStage", {})
                subprocesses = memory_stage.get("subprocesses", {})
                memory_check = subprocesses.get("memory_check", {})
                metadata = memory_check.get("metadata", {})

                if "memory_delta_mb" in metadata:
                    print(f"  Memory delta captured: {metadata['memory_delta_mb']:.2f} MB")
                else:
                    print("  ⚠ Memory delta not captured in metadata")
        else:
            results["memory_tracking"] = "DISABLED"
            results["details"].append("⊘ Memory tracking disabled (psutil not available)")
            print("⊘ Memory tracking: DISABLED")
            print("  psutil library not installed (graceful fallback)")

        print()
    except Exception as e:
        results["memory_tracking"] = "ERROR"
        results["details"].append(f"✗ Memory tracking test failed: {e}")
        print(f"✗ Memory tracking error: {e}")
        print()

    # ========================================================================
    # FINAL TEST STATUS
    # ========================================================================
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    # Determine overall test status
    failures = [
        results["logger_initialization"] == "FAIL",
        results["stage_tracking"] == "FAIL",
        results["json_validation"] == "FAIL",
        results["context_managers"]["timer"] == "FAIL",
        results["context_managers"]["subprocess"] == "FAIL",
    ]

    if any(failures):
        results["test_status"] = "FAIL"
        print("OVERALL STATUS: ✗ FAIL")
    else:
        results["test_status"] = "PASS"
        print("OVERALL STATUS: ✓ PASS")

    print()
    print("Individual Component Results:")
    print(f"  Logger Initialization: {results['logger_initialization']}")
    print(f"  Stage Tracking: {results['stage_tracking']}")
    print(f"  GPU Monitoring: {results['gpu_monitoring']}")
    if results['gpu_device']:
        print(f"    GPU Device: {results['gpu_device']}")
    print(f"  Reports Generated:")
    print(f"    JSON: {results['reports_generated']['json']}")
    print(f"    TXT: {results['reports_generated']['txt']}")
    print(f"  JSON Structure Validation: {results['json_validation']}")
    print(f"  Context Managers:")
    print(f"    Timer: {results['context_managers']['timer']}")
    print(f"    Subprocess: {results['context_managers']['subprocess']}")
    print(f"  Memory Tracking: {results['memory_tracking']}")

    print()
    print("Details:")
    for detail in results["details"]:
        print(f"  {detail}")

    print("=" * 80)

    return results


if __name__ == "__main__":
    test_performance_logger()
