#!/usr/bin/env python3
"""
Test GPU provider detection and configuration
"""

import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gpu_config import detect_provider, get_optimal_config, GPUProvider


class TestGPUProviderDetection(unittest.TestCase):
    """Test GPU provider auto-detection"""

    def test_cuda_available(self):
        """Test that CUDA is available"""
        import torch
        self.assertTrue(torch.cuda.is_available(), "CUDA must be available for GPU tests")

    def test_detect_provider_returns_valid_enum(self):
        """Test that provider detection returns valid enum"""
        provider = detect_provider()
        self.assertIsInstance(provider, GPUProvider)
        self.assertIn(provider, list(GPUProvider))

    def test_get_optimal_config(self):
        """Test that optimal config is generated"""
        config = get_optimal_config()

        # Verify all fields populated
        self.assertIsNotNone(config.provider)
        self.assertIsNotNone(config.device_name)
        self.assertGreater(config.vram_gb, 0)
        self.assertIn(config.compute_type, ["float16", "int8", "float32"])
        self.assertGreater(config.batch_size, 0)
        self.assertTrue(os.path.exists(os.path.dirname(config.model_cache_dir)))

    def test_compute_type_selection(self):
        """Test that compute type is selected appropriately"""
        config = get_optimal_config()

        # A100/H100 should use float16
        if "A100" in config.device_name or "H100" in config.device_name:
            self.assertEqual(config.compute_type, "float16")
            self.assertTrue(config.enable_tf32)

        # RTX should use int8
        elif "RTX" in config.device_name:
            self.assertEqual(config.compute_type, "int8")

    def test_model_cache_dir_created(self):
        """Test that model cache directory exists"""
        config = get_optimal_config()

        # Directory should be created
        self.assertTrue(os.path.exists(config.model_cache_dir) or
                       os.path.exists(os.path.dirname(config.model_cache_dir)))

    def test_environment_variables_set(self):
        """Test that cache environment variables are set"""
        config = get_optimal_config()
        self.assertEqual(os.environ.get('TRANSFORMERS_CACHE'), config.model_cache_dir)
        self.assertEqual(os.environ.get('HF_HOME'), config.model_cache_dir)


class TestGPUConfigOptimization(unittest.TestCase):
    """Test GPU configuration optimization"""

    def test_vram_detection(self):
        """Test that VRAM is correctly detected"""
        import torch

        config = get_optimal_config()
        actual_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3

        self.assertAlmostEqual(config.vram_gb, actual_vram, delta=0.5)

    def test_batch_size_scales_with_gpu(self):
        """Test that batch size is appropriate for GPU"""
        config = get_optimal_config()

        # Larger GPUs should have larger batch sizes
        if config.vram_gb >= 40:  # A100
            self.assertGreaterEqual(config.batch_size, 8)
        elif config.vram_gb >= 24:  # RTX 3090/4090
            self.assertGreaterEqual(config.batch_size, 4)


def main():
    # Print GPU info first
    print("\n" + "="*60)
    print("GPU Information")
    print("="*60)

    import torch
    print(f"CUDA Available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"CUDA Version: {torch.version.cuda}")

    from gpu_config import print_gpu_info
    print()
    print_gpu_info()
    print()

    # Run tests
    unittest.main(argv=[''], verbosity=2)


if __name__ == "__main__":
    main()
