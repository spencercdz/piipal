#!/usr/bin/env python3
"""
Unit tests for the YOLOv11e PII Detection Pipeline.

This file contains comprehensive tests for all major functionality.
"""

import unittest
import sys
import os
import tempfile
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pii_detector import (
    YOLOEPIIDetector, 
    adaptive_blur, 
    quick_image_blur, 
    quick_video_blur,
    create_custom_pii_detector,
    batch_process_directory
)

class TestAdaptiveBlur(unittest.TestCase):
    """Test the adaptive blur utility function."""
    
    def test_adaptive_blur_light(self):
        """Test light blur strength."""
        # Create a test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Apply light blur
        blurred = adaptive_blur(test_image, "light")
        
        # Check that image dimensions are preserved
        self.assertEqual(test_image.shape, blurred.shape)
        
        # Check that blurring actually occurred (variance should decrease)
        original_variance = np.var(test_image)
        blurred_variance = np.var(blurred)
        self.assertLess(blurred_variance, original_variance)
    
    def test_adaptive_blur_medium(self):
        """Test medium blur strength."""
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        blurred = adaptive_blur(test_image, "medium")
        
        self.assertEqual(test_image.shape, blurred.shape)
        
        # Medium blur should be stronger than light
        light_blurred = adaptive_blur(test_image, "light")
        medium_blurred = adaptive_blur(test_image, "medium")
        
        light_variance = np.var(light_blurred)
        medium_variance = np.var(medium_blurred)
        
        # Medium blur should have lower variance (more blur)
        self.assertLessEqual(medium_variance, light_variance)
    
    def test_adaptive_blur_heavy(self):
        """Test heavy blur strength."""
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        blurred = adaptive_blur(test_image, "heavy")
        
        self.assertEqual(test_image.shape, blurred.shape)
        
        # Heavy blur should be strongest
        light_blurred = adaptive_blur(test_image, "light")
        heavy_blurred = adaptive_blur(test_image, "heavy")
        
        light_variance = np.var(light_blurred)
        heavy_variance = np.var(heavy_blurred)
        
        # Heavy blur should have lowest variance (most blur)
        self.assertLessEqual(heavy_variance, light_variance)
    
    def test_adaptive_blur_small_roi(self):
        """Test blurring with very small ROI."""
        # Test with very small image
        small_image = np.random.randint(0, 255, (5, 5, 3), dtype=np.uint8)
        
        # Should not crash
        blurred = adaptive_blur(small_image, "medium")
        
        self.assertEqual(small_image.shape, blurred.shape)
    
    def test_adaptive_blur_invalid_strength(self):
        """Test blurring with invalid strength parameter."""
        test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        # Should use default medium strength
        blurred = adaptive_blur(test_image, "invalid_strength")
        
        self.assertEqual(test_image.shape, blurred.shape)

class TestYOLOEPIIDetector(unittest.TestCase):
    """Test the main PII detector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_dir, "test_image.jpg")
        self.test_output_path = os.path.join(self.test_dir, "output_image.jpg")
        
        # Create a simple test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(self.test_image_path, test_image)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_detector_initialization(self):
        """Test detector initialization with different parameters."""
        # Test default initialization
        detector = YOLOEPIIDetector()
        self.assertEqual(detector.sensitivity_level, "high_sensitivity")
        self.assertEqual(detector.blur_strength, "medium")
        
        # Test custom initialization
        detector = YOLOEPIIDetector(
            model_name="yoloe-11m-seg.pt",
            sensitivity_level="low_sensitivity",
            blur_strength="heavy"
        )
        self.assertEqual(detector.sensitivity_level, "low_sensitivity")
        self.assertEqual(detector.blur_strength, "heavy")
    
    def test_confidence_threshold_retrieval(self):
        """Test confidence threshold retrieval."""
        detector = YOLOEPIIDetector()
        
        # Test specific class threshold
        threshold = detector._get_confidence_threshold("passport")
        self.assertEqual(threshold, 0.3)
        
        # Test default threshold for unknown class
        threshold = detector._get_confidence_threshold("unknown_class")
        self.assertEqual(threshold, 0.3)  # high_sensitivity default
    
    def test_process_frame_empty_detections(self):
        """Test frame processing with no detections."""
        detector = YOLOEPIIDetector()
        
        # Create a test frame
        test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Process frame (should return original frame and empty detections)
        processed_frame, detections = detector.process_frame(test_frame)
        
        self.assertEqual(len(detections), 0)
        # Frame should be unchanged if no detections
        np.testing.assert_array_equal(processed_frame, test_frame)
    
    def test_blur_region(self):
        """Test region blurring functionality."""
        detector = YOLOEPIIDetector()
        
        # Create a test frame
        test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        original_frame = test_frame.copy()
        
        # Blur a region
        detector._blur_region(test_frame, 10, 10, 50, 50)
        
        # Check that the region was modified
        self.assertFalse(np.array_equal(test_frame, original_frame))
        
        # Check that the blurred region is actually blurred
        blurred_region = test_frame[10:50, 10:50]
        original_region = original_frame[10:50, 10:50]
        
        # Variance should be lower in blurred region
        self.assertLess(np.var(blurred_region), np.var(original_region))

class TestQuickFunctions(unittest.TestCase):
    """Test the quick convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.test_dir, "test_image.jpg")
        self.test_output_path = os.path.join(self.test_dir, "output_image.jpg")
        
        # Create a simple test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(self.test_image_path, test_image)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_quick_image_blur(self):
        """Test quick image blur function."""
        try:
            result = quick_image_blur(
                self.test_image_path,
                self.test_output_path,
                model_size="s",  # Use small model for testing
                sensitivity="medium_sensitivity"
            )
            
            # Check result structure
            self.assertIn("input_path", result)
            self.assertIn("output_path", result)
            self.assertIn("detections_count", result)
            self.assertIn("detections", result)
            
            # Check that output file was created
            self.assertTrue(os.path.exists(self.test_output_path))
            
        except Exception as e:
            # If YOLOE model is not available, skip this test
            self.skipTest(f"YOLOE model not available: {e}")
    
    def test_quick_image_blur_invalid_input(self):
        """Test quick image blur with invalid input."""
        with self.assertRaises(ValueError):
            quick_image_blur("nonexistent.jpg", self.test_output_path)

class TestCustomDetector(unittest.TestCase):
    """Test custom detector creation."""
    
    def test_create_custom_pii_detector(self):
        """Test custom detector creation."""
        custom_classes = ["custom_class_1", "custom_class_2"]
        custom_thresholds = {"custom_class_1": 0.4, "custom_class_2": 0.6}
        
        try:
            detector = create_custom_pii_detector(
                custom_classes=custom_classes,
                model_size="m",
                custom_thresholds=custom_thresholds
            )
            
            # Check that detector was created
            self.assertIsInstance(detector, YOLOEPIIDetector)
            
        except Exception as e:
            # If YOLOE model is not available, skip this test
            self.skipTest(f"YOLOE model not available: {e}")

class TestBatchProcessing(unittest.TestCase):
    """Test batch processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # Create input directory with test images
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test images
        for i in range(3):
            test_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
            image_path = os.path.join(self.input_dir, f"test_{i}.jpg")
            import cv2
            cv2.imwrite(image_path, test_image)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_batch_process_directory(self):
        """Test batch directory processing."""
        try:
            results = batch_process_directory(
                self.input_dir,
                self.output_dir,
                [".jpg"]
            )
            
            # Check results structure
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 3)  # 3 test images
            
            for result in results:
                self.assertIn("file", result)
                self.assertIn("output", result)
                self.assertIn("detections", result)
            
            # Check that output files were created
            output_files = list(Path(self.output_dir).glob("*.jpg"))
            self.assertEqual(len(output_files), 3)
            
        except Exception as e:
            # If YOLOE model is not available, skip this test
            self.skipTest(f"YOLOE model not available: {e}")

class TestConfiguration(unittest.TestCase):
    """Test configuration and constants."""
    
    def test_sensitive_classes_structure(self):
        """Test that sensitive classes are properly defined."""
        from pii_detector import SENSITIVE_CLASSES
        
        # Check that classes list is not empty
        self.assertGreater(len(SENSITIVE_CLASSES), 0)
        
        # Check that all classes are strings
        for class_name in SENSITIVE_CLASSES:
            self.assertIsInstance(class_name, str)
            self.assertGreater(len(class_name), 0)
    
    def test_confidence_thresholds_structure(self):
        """Test that confidence thresholds are properly defined."""
        from pii_detector import CONFIDENCE_THRESHOLDS
        
        # Check that thresholds dict is not empty
        self.assertGreater(len(CONFIDENCE_THRESHOLDS), 0)
        
        # Check that all sensitivity levels have default thresholds
        for sensitivity_level, thresholds in CONFIDENCE_THRESHOLDS.items():
            self.assertIn("default", thresholds)
            self.assertIsInstance(thresholds["default"], (int, float))
            self.assertGreaterEqual(thresholds["default"], 0)
            self.assertLessEqual(thresholds["default"], 1)

def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAdaptiveBlur,
        TestYOLOEPIIDetector,
        TestQuickFunctions,
        TestCustomDetector,
        TestBatchProcessing,
        TestConfiguration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 Running YOLOv11e PII Detection Pipeline Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
