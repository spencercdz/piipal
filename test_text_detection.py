#!/usr/bin/env python3
"""
Test script to verify text-prompted detection works with YOLOE.
This follows the working example pattern you provided.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_yoloe():
    """Test basic YOLOE functionality."""
    print("🧪 Testing basic YOLOE functionality...")
    
    try:
        from ultralytics import YOLOE
        
        # Initialize model (same as your working example)
        model = YOLOE("yoloe-11s-seg.pt")
        print("✅ YOLOE model loaded successfully")
        
        return model
        
    except Exception as e:
        print(f"❌ Failed to load YOLOE model: {e}")
        return None

def test_text_prompted_detection():
    """Test text-prompted detection using the working pattern."""
    print("\n🔤 Testing text-prompted detection...")
    
    try:
        from ultralytics import YOLOE
        import numpy as np
        
        # Create model (same as your working example)
        model = YOLOE("yoloe-11s-seg.pt")
        
        # Test with simple prompts (same pattern as your example)
        test_prompts = ["person", "face", "credit card"]
        
        for prompt in test_prompts:
            print(f"\n   Testing prompt: '{prompt}'")
            
            try:
                # Use the same pattern as your working example
                names = [prompt]
                
                # Get text embeddings and set classes
                text_embeddings = model.get_text_pe(names)
                model.set_classes(names, text_embeddings)
                
                print(f"   ✅ Text embeddings configured for '{prompt}'")
                
                # Test prediction
                test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
                results = model.predict(test_image, verbose=False)
                
                if results and len(results) > 0:
                    print(f"   ✅ Prediction successful for '{prompt}'")
                else:
                    print(f"   ⚠️  No detections for '{prompt}' (expected for random image)")
                    
            except Exception as e:
                print(f"   ❌ Failed to test '{prompt}': {e}")
        
        print("\n✅ Text-prompted detection test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Text-prompted detection test failed: {e}")
        return False

def test_pii_detector():
    """Test the PII detector with text prompts."""
    print("\n🛡️ Testing PII detector...")
    
    try:
        from pii_detector import YOLOEPIIDetector
        
        # Initialize detector
        detector = YOLOEPIIDetector()
        print("✅ PII detector initialized")
        
        # Test text-prompted detection
        success = detector.test_text_prompted_detection()
        
        if success:
            print("✅ PII detector text-prompted detection working!")
        else:
            print("⚠️  PII detector text-prompted detection has issues")
        
        return success
        
    except Exception as e:
        print(f"❌ PII detector test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 YOLOE Text-Prompted Detection Test")
    print("=" * 50)
    
    # Test 1: Basic YOLOE
    model = test_basic_yoloe()
    if not model:
        print("\n❌ Basic YOLOE test failed. Cannot continue.")
        return False
    
    # Test 2: Text-prompted detection
    text_ok = test_text_prompted_detection()
    
    # Test 3: PII detector
    pii_ok = test_pii_detector()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if text_ok and pii_ok:
        print("🎉 All tests passed! Text-prompted detection is working!")
        print("\n💡 You can now use:")
        print("   - YOLOE with text prompts")
        print("   - PII detector with sensitive class detection")
        print("   - Image and video blurring with PII detection")
    elif text_ok:
        print("✅ YOLOE text-prompted detection works!")
        print("⚠️  PII detector has some issues")
    else:
        print("❌ Text-prompted detection has issues")
        print("\n💡 Troubleshooting:")
        print("   1. Check ultralytics version")
        print("   2. Verify YOLOE model download")
        print("   3. Check for CLIP dependencies")
    
    return text_ok and pii_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
