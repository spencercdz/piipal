# YOLOv11e PII Detection Pipeline

A powerful and efficient PII (Personally Identifiable Information) detection and blurring system using YOLOv11e (YOLOE) for open-vocabulary object detection.

## Features

- **Open-vocabulary Detection**: Uses YOLOE's text-prompted detection for flexible PII class identification
- **Multi-modal Support**: Process both images and videos
- **Adaptive Blurring**: Intelligent Gaussian blur with configurable intensity levels
- **Configurable Sensitivity**: Multiple sensitivity profiles for different use cases
- **Real-time Processing**: Efficient video processing with optional frame skipping
- **Custom Classes**: Easy configuration of custom PII detection classes

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd techjam_catgpt_2025
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. The YOLOv11e model will be automatically downloaded on first use.

## Quick Start

### Basic Image Processing
```python
from pii_detector import quick_image_blur

# Blur PII in an image
result = quick_image_blur("input.jpg", "output_blurred.jpg")
print(f"Found {result['detections_count']} PII elements")
```

### Basic Video Processing
```python
from pii_detector import quick_video_blur

# Blur PII in a video
result = quick_video_blur("input.mp4", "output_blurred.mp4")
print(f"Processed {result['frames_processed']} frames")
```

### Advanced Usage
```python
from pii_detector import YOLOEPIIDetector

# Initialize detector with custom settings
detector = YOLOEPIIDetector(
    model_name="yoloe-11l-seg.pt",
    sensitivity_level="high_sensitivity",
    blur_strength="medium"
)

# Process image
detections = detector.process_image("input.jpg", "output.jpg")
```

## Configuration

### Sensitivity Levels
- **high_sensitivity**: Lower confidence thresholds for maximum PII detection
- **medium_sensitivity**: Balanced detection with moderate thresholds
- **low_sensitivity**: Higher confidence thresholds for precision

### Blur Strengths
- **light**: Subtle blurring
- **medium**: Standard blurring (default)
- **heavy**: Strong blurring

### Model Sizes
- **yoloe-11s-seg.pt**: Small model (fastest, lower accuracy)
- **yoloe-11m-seg.pt**: Medium model (balanced)
- **yoloe-11l-seg.pt**: Large model (highest accuracy, slower)

## Supported PII Classes

The system detects various types of sensitive information:

- **Identity Documents**: Passports, driver licenses, ID cards, credit cards
- **Personal Information**: Phone numbers, email addresses, signatures
- **Financial Documents**: Bank statements, receipts, invoices
- **Medical Records**: Prescriptions, health cards
- **Biometric Data**: Faces, fingerprints
- **Digital Displays**: Screens showing sensitive information

## Examples

### Custom PII Classes
```python
from pii_detector import create_custom_pii_detector

custom_classes = ["credit card", "passport", "face"]
custom_thresholds = {"credit card": 0.3, "passport": 0.2}

detector = create_custom_pii_detector(custom_classes, "m", custom_thresholds)
```

### Batch Processing
```python
from pii_detector import batch_process_directory

# Process all images in a directory
results = batch_process_directory("input_folder/", "output_folder/")
```

## Project Structure

```
techjam_catgpt_2025/
├── pii_detector.py          # Main PII detection module
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── examples/                # Usage examples
│   ├── basic_usage.py
│   ├── custom_classes.py
│   └── batch_processing.py
├── tests/                   # Unit tests
│   └── test_pii_detector.py
├── config/                  # Configuration files
│   └── pii_classes.json
└── data/                    # Sample data (not included)
    ├── sample_images/
    └── sample_videos/
```

## Performance

- **Image Processing**: ~0.1-2 seconds per image (depending on model size)
- **Video Processing**: ~5-30 FPS (depending on model size and frame skip)
- **Memory Usage**: 2-8 GB RAM (depending on model size)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Ultralytics YOLOv11e](https://github.com/ultralytics/ultralytics)
- OpenCV for computer vision operations
- PyTorch for deep learning backend
