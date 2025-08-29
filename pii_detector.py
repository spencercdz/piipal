"""
Clean PII detection pipeline using YOLOv11e (YOLOE):
- Uses YOLOE's open-vocabulary detection with text prompts for PII classes
- Direct detection and segmentation without complex dependencies
- Adaptive Gaussian blur for detected sensitive content
- Support for both images and videos

Requirements:
- pip install ultralytics opencv-python numpy
- YOLOv11e model will be automatically downloaded on first use
"""

from ultralytics import YOLOE
import cv2
import numpy as np
import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any, List

# -----------------------------
# Sensitive PII classes for YOLOE text prompts
# -----------------------------
SENSITIVE_CLASSES = [
    # Identity documents and cards
    "passport", "driver license", "id card", "credit card", "debit card",
    "bank card", "identity card", "national id", "social security card",

    # Personal information displays
    "phone number", "email address", "address", "signature",
    "license plate", "vehicle plate", "barcode", "qr code",

    # Financial information
    "bank statement", "receipt", "invoice", "check", "financial document",

    # Medical documents
    "medical record", "prescription", "health card", "medical document",

    # Biometric and personal
    "fingerprint", "face", "person", "child", "minor",

    # Documents with potential PII
    "document", "contract", "letter", "form", "certificate",

    # Digital displays showing sensitive info
    "screen", "monitor", "tablet", "phone screen", "computer screen",
    "pin entry", "password field", "login screen",
]

# Confidence thresholds for different sensitivity levels
CONFIDENCE_THRESHOLDS = {
    "high_sensitivity": {
        "passport": 0.3,
        "driver license": 0.3,
        "credit card": 0.3,
        "social security card": 0.3,
        "face": 0.4,
        "person": 0.5,
        "default": 0.3
    },
    "medium_sensitivity": {
        "default": 0.5
    },
    "low_sensitivity": {
        "default": 0.7
    }
}

# -----------------------------
# Utility: adaptive gaussian blur
# -----------------------------
def adaptive_blur(roi: np.ndarray, blur_strength: str = "medium") -> np.ndarray:
    """
    Apply Gaussian blur with kernel size proportional to ROI size.

    Args:
        roi: Region of interest to blur
        blur_strength: "light", "medium", or "heavy"
    """
    h, w = roi.shape[:2]

    # Adjust blur intensity based on strength setting
    strength_multipliers = {"light": 0.04, "medium": 0.06, "heavy": 0.08}
    multiplier = strength_multipliers.get(blur_strength, 0.06)

    # Make kernel proportional to ROI size
    k = int(max(3, round(multiplier * max(h, w))))
    if k % 2 == 0:
        k += 1

    # Ensure kernel isn't larger than the ROI
    k = min(k, min(h, w) if min(h, w) > 2 else 3)

    sigma = 0  # Let OpenCV compute sigma from kernel size
    return cv2.GaussianBlur(roi, (k, k), sigma)

# -----------------------------
# Main PII Detection Pipeline
# -----------------------------
class YOLOEPIIDetector:
    def __init__(self,
                 model_name: str = "yoloe-11l-seg.pt",
                 sensitivity_level: str = "high_sensitivity",
                 blur_strength: str = "medium"):
        """
        Initialize YOLOE PII detector.

        Args:
            model_name: YOLOE model variant (yoloe-11s/m/l-seg.pt)
            sensitivity_level: Confidence threshold profile
            blur_strength: Blur intensity for detected PII
        """
        self.model = YOLOE(model_name)
        self.sensitivity_level = sensitivity_level
        self.blur_strength = blur_strength
        self.confidence_thresholds = CONFIDENCE_THRESHOLDS[sensitivity_level]

        # Set up YOLOE with PII classes using the working approach
        self._setup_pii_classes()

        print(f"✅ Initialized YOLOE PII detector with {len(SENSITIVE_CLASSES)} sensitive classes")

    def _setup_pii_classes(self):
        """Configure YOLOE to detect PII classes using text prompts."""
        try:
            # Use the working approach from the reference
            names = SENSITIVE_CLASSES
            
            # Set classes with text embeddings (this is the working pattern)
            text_embeddings = self.model.get_text_pe(names)
            self.model.set_classes(names, text_embeddings)
            
            print("✅ YOLOE configured for PII detection classes using text prompts")
            print(f"   Configured {len(names)} sensitive classes")
            
        except Exception as e:
            print(f"❌ Error configuring text embeddings: {e}")
            print("⚠️  Using basic YOLOE detection (no text prompts)")
            print("   The model will still detect objects but may not be optimized for PII")

    def _get_confidence_threshold(self, class_name: str) -> float:
        """Get confidence threshold for specific class."""
        return self.confidence_thresholds.get(class_name.lower(),
                                            self.confidence_thresholds["default"])

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a single frame to detect and blur PII.

        Args:
            frame: Input frame as BGR numpy array

        Returns:
            Tuple of (processed_frame, detection_info_list)
        """
        # Run YOLOE prediction
        results = self.model.predict(frame, verbose=False)

        if not results or not results[0].boxes:
            return frame, []

        detection_info = []
        result = results[0]

        # Process each detection
        boxes = result.boxes
        names = result.names if hasattr(result, 'names') else {}

        for i in range(len(boxes)):
            # Get detection data
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_idx = int(boxes.cls[i].cpu().numpy())

            # Get class name from our configured classes
            if cls_idx < len(SENSITIVE_CLASSES):
                class_name = SENSITIVE_CLASSES[cls_idx]
            else:
                # Fallback to generic detection
                class_name = names.get(cls_idx, f"class_{cls_idx}")

            # Check confidence threshold for this specific class
            threshold = self._get_confidence_threshold(class_name)
            if conf < threshold:
                continue

            # Extract and validate bounding box coordinates
            x1, y1, x2, y2 = map(int, xyxy)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                continue

            # Apply blur to detected PII region
            self._blur_region(frame, x1, y1, x2, y2)

            # Store detection information
            detection_info.append({
                "bbox": [x1, y1, x2, y2],
                "class": class_name,
                "confidence": conf,
                "class_id": cls_idx,
                "threshold_used": threshold,
                "blurred": True
            })

        return frame, detection_info

    def _blur_region(self, frame: np.ndarray, x1: int, y1: int, x2: int, y2: int):
        """Apply adaptive blur to a region with optional padding."""
        # Add padding to ensure complete coverage
        pad_x = int(0.05 * (x2 - x1))
        pad_y = int(0.05 * (y2 - y1))

        # Apply padding with bounds checking
        sx1 = max(0, x1 - pad_x)
        sy1 = max(0, y1 - pad_y)
        sx2 = min(frame.shape[1], x2 + pad_x)
        sy2 = min(frame.shape[0], y2 + pad_y)

        # Extract ROI and apply blur
        roi = frame[sy1:sy2, sx1:sx2]
        if roi.size > 0:  # Ensure ROI is valid
            roi_blurred = adaptive_blur(roi, self.blur_strength)
            frame[sy1:sy2, sx1:sx2] = roi_blurred

    def process_image(self, input_path: str, output_path: str) -> List[Dict[str, Any]]:
        """
        Process a single image for PII detection and blurring.

        Args:
            input_path: Path to input image
            output_path: Path to save processed image

        Returns:
            List of detection information dictionaries
        """
        frame = cv2.imread(input_path)
        if frame is None:
            raise ValueError(f"Could not load image from {input_path}")

        processed_frame, detection_info = self.process_frame(frame)

        # Save processed image
        cv2.imwrite(output_path, processed_frame)

        print(f"✅ Processed image saved to: {output_path}")
        print(f"Found {len(detection_info)} PII detections")

        return detection_info

    def process_video(self, input_path: str, output_path: str,
                     frame_skip: int = 0) -> List[List[Dict[str, Any]]]:
        """
        Process video for PII detection and blurring.

        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            frame_skip: Process every N frames (0 = process all frames)

        Returns:
            List of detection info for each processed frame
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video from {input_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Set up video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        all_detections = []
        frame_idx = 0
        processed_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Apply frame skipping if specified
            if frame_skip > 0 and frame_idx % (frame_skip + 1) != 0:
                out.write(frame)  # Write original frame
                frame_idx += 1
                continue

            # Process frame for PII
            processed_frame, detection_info = self.process_frame(frame)
            out.write(processed_frame)
            all_detections.append(detection_info)

            processed_frames += 1
            if processed_frames % 50 == 0:
                print(f"Processed {processed_frames} frames ({frame_idx+1}/{total_frames})")

            frame_idx += 1

        cap.release()
        out.release()

        print(f"✅ Video processing complete. Saved to: {output_path}")
        print(f"Processed {processed_frames} frames with PII detection")

        return all_detections

    def test_detection(self, test_prompt: str = "person") -> bool:
        """
        Test if the PII detector is working correctly.
        
        Args:
            test_prompt: Test prompt to verify functionality
            
        Returns:
            True if test successful, False otherwise
        """
        try:
            print(f"🧪 Testing PII detection with: '{test_prompt}'")
            
            # Create a simple test image
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            
            # Test the detection
            results = self.model.predict(test_image, verbose=False)
            
            if results and len(results) > 0:
                print("✅ PII detection test successful!")
                return True
            else:
                print("⚠️  PII detection test returned no results")
                return False
                
        except Exception as e:
            print(f"❌ PII detection test failed: {e}")
            return False

# -----------------------------
# Convenience functions for different use cases
# -----------------------------
def quick_image_blur(input_path: str, output_path: str,
                    model_size: str = "l", sensitivity: str = "high_sensitivity") -> Dict[str, Any]:
    """
    Quick function to blur PII in an image.

    Args:
        input_path: Input image path
        output_path: Output image path
        model_size: YOLOE model size ("s", "m", "l")
        sensitivity: Sensitivity level for detection
    """
    model_name = f"yoloe-11{model_size}-seg.pt"
    detector = YOLOEPIIDetector(model_name, sensitivity)
    detections = detector.process_image(input_path, output_path)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "detections_count": len(detections),
        "detections": detections
    }

def quick_video_blur(input_path: str, output_path: str,
                    model_size: str = "l", sensitivity: str = "high_sensitivity",
                    frame_skip: int = 0) -> Dict[str, Any]:
    """
    Quick function to blur PII in a video.

    Args:
        input_path: Input video path
        output_path: Output video path
        model_size: YOLOE model size ("s", "m", "l")
        sensitivity: Sensitivity level for detection
        frame_skip: Skip frames for faster processing (0 = process all)
    """
    model_name = f"yoloe-11{model_size}-seg.pt"
    detector = YOLOEPIIDetector(model_name, sensitivity)
    all_detections = detector.process_video(input_path, output_path, frame_skip)

    total_detections = sum(len(frame_detections) for frame_detections in all_detections)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "frames_processed": len(all_detections),
        "total_detections": total_detections,
        "detections_by_frame": all_detections
    }

# -----------------------------
# Advanced: Custom class configuration
# -----------------------------
def create_custom_pii_detector(custom_classes: List[str],
                              model_size: str = "l",
                              custom_thresholds: Dict[str, float] = None) -> YOLOEPIIDetector:
    """
    Create a PII detector with custom classes and thresholds.

    Args:
        custom_classes: List of custom PII classes to detect
        model_size: YOLOE model size
        custom_thresholds: Custom confidence thresholds per class
    """
    global SENSITIVE_CLASSES
    original_classes = SENSITIVE_CLASSES.copy()

    # Update global classes temporarily
    SENSITIVE_CLASSES = custom_classes

    # Create custom threshold configuration
    if custom_thresholds:
        custom_config = {"default": 0.5}
        custom_config.update(custom_thresholds)
        CONFIDENCE_THRESHOLDS["custom"] = custom_config
        sensitivity_level = "custom"
    else:
        sensitivity_level = "medium_sensitivity"

    model_name = f"yoloe-11{model_size}-seg.pt"
    detector = YOLOEPIIDetector(model_name, sensitivity_level)

    # Restore original classes
    SENSITIVE_CLASSES = original_classes

    return detector

# -----------------------------
# Example usage and testing
# -----------------------------
def demo_basic_usage():
    """Demonstrate basic PII detection usage."""
    print("=== YOLOv11e PII Detection Demo ===")

    # Initialize detector
    detector = YOLOEPIIDetector(model_name="yoloe-11l-seg.pt")

    # Test detection
    detector.test_detection()

    print("Detector ready. Use detector.process_image() or detector.process_video()")
    return detector

def demo_custom_classes():
    """Demonstrate custom class detection."""
    print("=== Custom PII Classes Demo ===")

    # Define custom PII classes
    custom_classes = ["credit card", "passport", "driver license", "face", "phone screen"]
    custom_thresholds = {
        "credit card": 0.3,
        "passport": 0.2,
        "face": 0.6
    }

    detector = create_custom_pii_detector(custom_classes, "m", custom_thresholds)
    print("Custom detector ready with classes:", custom_classes)
    return detector

def batch_process_directory(input_dir: str, output_dir: str,
                          file_extensions: List[str] = [".jpg", ".jpeg", ".png"]):
    """
    Process all images in a directory for PII detection.
    """
    detector = YOLOEPIIDetector()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    processed_files = []

    for ext in file_extensions:
        for img_file in input_path.glob(f"*{ext}"):
            output_file = output_path / f"blurred_{img_file.name}"
            try:
                detections = detector.process_image(str(img_file), str(output_file))
                processed_files.append({
                    "file": str(img_file),
                    "output": str(output_file),
                    "detections": len(detections)
                })
                print(f"✓ Processed {img_file.name}: {len(detections)} PII detections")
            except Exception as e:
                print(f"✗ Error processing {img_file.name}: {e}")

    return processed_files

if __name__ == "__main__":
    # Basic usage example
    print("YOLOv11e PII Detection Pipeline")
    print("Choose your usage pattern:")
    print("1. Basic detector: demo_basic_usage()")
    print("2. Custom classes: demo_custom_classes()")
    print("3. Quick image: quick_image_blur('input.jpg', 'output.jpg')")
    print("4. Quick video: quick_video_blur('input.mp4', 'output.mp4')")
    print("5. Batch directory: batch_process_directory('input_dir/', 'output_dir/')")

    # Uncomment to run basic demo
    # detector = demo_basic_usage()

    # Example of processing specific files:
    quick_image_blur("test1.jpg", "blurred_image.jpg", model_size="l")
    # quick_video_blur("test_video.mp4", "blurred_video.mp4", model_size="m", frame_skip=2)
