#!/usr/bin/env python3
"""
Command-line interface for the YOLOv11e PII Detection Pipeline.

Usage:
    python cli.py image <input> <output> [options]
    python cli.py video <input> <output> [options]
    python cli.py batch <input_dir> <output_dir> [options]
"""

import argparse
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pii_detector import (
    YOLOEPIIDetector,
    quick_image_blur,
    quick_video_blur,
    batch_process_directory
)

def validate_file_path(file_path, file_type="file"):
    """Validate that a file path exists and is accessible."""
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_type} not found: {file_path}")
        return False
    return True

def validate_directory_path(dir_path, create_if_missing=False):
    """Validate that a directory path exists and is accessible."""
    if not os.path.exists(dir_path):
        if create_if_missing:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✓ Created directory: {dir_path}")
                return True
            except Exception as e:
                print(f"❌ Error: Could not create directory {dir_path}: {e}")
                return False
        else:
            print(f"❌ Error: Directory not found: {dir_path}")
            return False
    return True

def process_image_command(args):
    """Process a single image."""
    print(f"🖼️  Processing image: {args.input}")
    
    # Validate input file
    if not validate_file_path(args.input, "Input image"):
        return 1
    
    # Validate/create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not validate_directory_path(output_dir, create_if_missing=True):
        return 1
    
    try:
        # Process image
        result = quick_image_blur(
            input_path=args.input,
            output_path=args.output,
            model_size=args.model_size,
            sensitivity=args.sensitivity
        )
        
        print(f"✅ Image processed successfully!")
        print(f"   Output: {result['output_path']}")
        print(f"   PII detections: {result['detections_count']}")
        
        if result['detections']:
            print("   Detected classes:")
            for det in result['detections']:
                print(f"     - {det['class']} ({det['confidence']:.2f})")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return 1

def process_video_command(args):
    """Process a video file."""
    print(f"🎥 Processing video: {args.input}")
    
    # Validate input file
    if not validate_file_path(args.input, "Input video"):
        return 1
    
    # Validate/create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not validate_directory_path(output_dir, create_if_missing=True):
        return 1
    
    try:
        # Process video
        result = quick_video_blur(
            input_path=args.input,
            output_path=args.output,
            model_size=args.model_size,
            sensitivity=args.sensitivity,
            frame_skip=args.frame_skip
        )
        
        print(f"✅ Video processed successfully!")
        print(f"   Output: {result['output_path']}")
        print(f"   Frames processed: {result['frames_processed']}")
        print(f"   Total PII detections: {result['total_detections']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        return 1

def batch_process_command(args):
    """Process multiple files in a directory."""
    print(f"📁 Batch processing directory: {args.input_dir}")
    
    # Validate input directory
    if not validate_directory_path(args.input_dir):
        return 1
    
    # Validate/create output directory
    if not validate_directory_path(args.output_dir, create_if_missing=True):
        return 1
    
    try:
        # Process directory
        results = batch_process_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            file_extensions=args.extensions
        )
        
        print(f"✅ Batch processing complete!")
        print(f"   Files processed: {len(results)}")
        
        total_detections = sum(r['detections'] for r in results)
        print(f"   Total PII detections: {total_detections}")
        
        # Show summary by file
        for result in results:
            status = "✓" if result['detections'] > 0 else "○"
            print(f"   {status} {os.path.basename(result['file'])}: {result['detections']} detections")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        return 1

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="YOLOv11e PII Detection Pipeline - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single image
  python cli.py image input.jpg output.jpg --model-size m --sensitivity high

  # Process a video with frame skipping
  python cli.py video input.mp4 output.mp4 --model-size s --frame-skip 2

  # Batch process all images in a directory
  python cli.py batch input_dir/ output_dir/ --extensions jpg png

  # Quick image processing with defaults
  python cli.py image input.jpg output.jpg
        """
    )
    
    # Global options
    parser.add_argument(
        "--model-size", "-m",
        choices=["s", "m", "l"],
        default="l",
        help="YOLOE model size: s (fast), m (balanced), l (accurate) [default: l]"
    )
    
    parser.add_argument(
        "--sensitivity", "-s",
        choices=["high_sensitivity", "medium_sensitivity", "low_sensitivity"],
        default="high_sensitivity",
        help="Detection sensitivity level [default: high_sensitivity]"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Image command
    image_parser = subparsers.add_parser("image", help="Process a single image")
    image_parser.add_argument("input", help="Input image path")
    image_parser.add_argument("output", help="Output image path")
    
    # Video command
    video_parser = subparsers.add_parser("video", help="Process a video file")
    video_parser.add_argument("input", help="Input video path")
    video_parser.add_argument("output", help="Output video path")
    video_parser.add_argument(
        "--frame-skip", "-f",
        type=int,
        default=0,
        help="Skip frames for faster processing (0 = process all) [default: 0]"
    )
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Process multiple files in a directory")
    batch_parser.add_argument("input_dir", help="Input directory path")
    batch_parser.add_argument("output_dir", help="Output directory path")
    batch_parser.add_argument(
        "--extensions", "-e",
        nargs="+",
        default=["jpg", "jpeg", "png"],
        help="File extensions to process [default: jpg jpeg png]"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "image":
        return process_image_command(args)
    elif args.command == "video":
        return process_video_command(args)
    elif args.command == "batch":
        return batch_process_command(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
