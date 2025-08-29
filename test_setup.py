#!/usr/bin/env python3
"""
Simple test script to verify the PII detector setup.
Run this to check if all dependencies are working.
"""

import sys

def test_imports():
    """Test if all required packages can be imported."""
    print("🧪 Testing package imports...")
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLOE
        print("✅ Ultralytics imported successfully")
    except ImportError as e:
        print(f"❌ Ultralytics import failed: {e}")
        print("   This is expected if you haven't installed requirements yet")
        return False
    
    try:
        import torch
        print("✅ PyTorch imported successfully")
        print(f"   PyTorch version: {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without YOLOE model."""
    print("\n🔧 Testing basic functionality...")
    
    try:
        import numpy as np
        import cv2
        
        # Test numpy operations
        test_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        print("✅ NumPy array operations working")
        
        # Test OpenCV operations
        blurred = cv2.GaussianBlur(test_array, (5, 5), 0)
        print("✅ OpenCV blur operations working")
        
        # Test pathlib
        from pathlib import Path
        test_path = Path("test_file.txt")
        print("✅ Pathlib operations working")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_yoloe_availability():
    """Test if YOLOE models are available."""
    print("\n🤖 Testing YOLOE availability...")
    
    try:
        from ultralytics import YOLOE
        
        # Try to create a YOLOE instance (this will download the model)
        print("   Attempting to initialize YOLOE...")
        print("   Note: This may take a while on first run as it downloads the model")
        
        # Use small model for testing
        model = YOLOE("yoloe-11s-seg.pt")
        print("✅ YOLOE model loaded successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ YOLOE test failed: {e}")
        print("   This is expected if you haven't installed requirements yet")
        return False

def main():
    """Run all tests."""
    print("🚀 PII Detector Setup Test")
    print("=" * 40)
    
    # Test basic imports
    imports_ok = test_imports()
    
    # Test basic functionality
    basic_ok = test_basic_functionality()
    
    # Test YOLOE (optional)
    yoloe_ok = test_yoloe_availability()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST SUMMARY")
    print("=" * 40)
    
    if imports_ok and basic_ok:
        print("✅ Basic setup is working!")
        if yoloe_ok:
            print("✅ YOLOE is ready to use!")
            print("\n🎉 Everything is set up correctly!")
        else:
            print("⚠️  YOLOE not available yet")
            print("\n💡 To complete setup:")
            print("   1. Install requirements: pip3 install -r requirements.txt")
            print("   2. Run this test again")
    else:
        print("❌ Setup has issues")
        print("\n💡 Troubleshooting:")
        print("   1. Check Python installation: python3 --version")
        print("   2. Install requirements: pip3 install -r requirements.txt")
        print("   3. Run this test again")
    
    return imports_ok and basic_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
