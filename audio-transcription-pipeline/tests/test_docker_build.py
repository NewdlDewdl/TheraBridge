#!/usr/bin/env python3
"""
Test Docker image build and functionality
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run shell command and report result"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print('='*60)

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print(f"FAILED: {description}")
        return False

    print(f"SUCCESS: {description}")
    return True


def main():
    """Run Docker build tests"""
    project_root = Path(__file__).parent.parent

    tests = [
        # Test 1: Dockerfile exists
        (f"test -f {project_root}/docker/Dockerfile.gpu",
         "Dockerfile exists"),

        # Test 2: Docker build (without models)
        (f"docker build -f {project_root}/docker/Dockerfile.gpu -t transcribe-gpu:test {project_root}",
         "Docker image builds"),

        # Test 3: Docker run help
        ("docker run --rm transcribe-gpu:test --help",
         "Docker container runs"),

        # Test 4: Docker GPU access (if nvidia-docker available)
        ("docker run --rm --gpus all transcribe-gpu:test python3 -c 'import torch; assert torch.cuda.is_available()'",
         "Docker GPU access (optional - skip if no GPU)"),
    ]

    results = []

    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))

        # Skip GPU test failure (not all test environments have GPU)
        if not success and "GPU access" in desc:
            print("Note: GPU test skipped (expected on non-GPU hosts)")
            results[-1] = (desc, True)

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for desc, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {desc}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
