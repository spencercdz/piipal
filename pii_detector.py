import time

from typing import List, Tuple
import cv2
import numpy as np
from ultralytics import YOLOE

# Optional: SAHI for slice-based inference
try:
    from sahi.predict import get_sliced_prediction
    from sahi.auto_model import AutoDetectionModel
    SAHI_AVAILABLE = True
except Exception:
    SAHI_AVAILABLE = False


# -------------------- Configuration --------------------
SENSITIVE_CLASSES: List[str] = [
    "license plate",
    "identity card",
    "credit card",
    "bank card",
    "card",
    "watermark overlay stamp",
    "wedding invitation",
]

# Blur strength configuration (kernel must be odd numbers)
BLUR_KERNEL: Tuple[int, int] = (25, 25)
BLUR_SIGMA_X: int = 0

# Model weights and device
MODEL_WEIGHTS: str = "yoloe-11l-seg-pf.pt"
DEVICE: str = "mps"  # set to "cpu" if MPS/CUDA unavailable

# Inference tuning for small objects - PRIORITIZING ACCURACY
CONF_THRESHOLD: float = 0.05  # Very low threshold to catch all potential objects
IMG_SIZE: int = 2560          # Large inference size for small object detail
UPSAMPLE_SCALE: float = 2.0   # 2x upsampling for better small object detection
IOU_THRESHOLD: float = 0.3    # Lower IOU to allow overlapping detections (better recall)
TTA: bool = True             # Enable test-time augmentation for better accuracy

# SAHI configuration - OPTIMIZED FOR SMALL OBJECTS
USE_SAHI: bool = True
USE_SAHI_SEG: bool = True
SAHI_SLICE_HEIGHT: int = 384  # Smaller slices for small objects
SAHI_SLICE_WIDTH: int = 384   # Smaller slices for small objects
SAHI_OVERLAP_RATIO: float = 0.4  # High overlap to catch objects at slice boundaries

# I/O configuration (built-in, no CLI)
INPUT_PATH: str = "car_vid.mp4"  # can be image or video
OUTPUT_PATH: str = "car_vid_blurred.mp4"


def load_model(weights: str) -> YOLOE:
    model = YOLOE(weights)
    # Disable runs folder saving
    model.verbose = False
    return model


def read_image(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image at '{path}'")
    return img


def is_video(path: str) -> bool:
    video_exts = {
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg",
    }
    lower = path.lower()
    return any(lower.endswith(ext) for ext in video_exts)


def clamp_bbox(xyxy: Tuple[int, int, int, int], width: int, height: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = xyxy
    x1 = max(0, min(int(x1), width - 1))
    y1 = max(0, min(int(y1), height - 1))
    x2 = max(0, min(int(x2), width - 1))
    y2 = max(0, min(int(y2), height - 1))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return x1, y1, x2, y2


def extract_sensitive_boxes(result, target_names: List[str]) -> List[Tuple[int, int, int, int]]:
    boxes_xyxy: List[Tuple[int, int, int, int]] = []
    if not hasattr(result, "boxes") or result.boxes is None:
        return boxes_xyxy

    names_map = result.names if hasattr(result, "names") else {}
    for box in result.boxes:
        cls_idx = int(box.cls.item()) if hasattr(box, "cls") else None
        if cls_idx is None:
            continue
        cls_name = names_map.get(cls_idx, None)
        if cls_name is None or cls_name not in target_names:
            continue

        xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
        boxes_xyxy.append((x1, y1, x2, y2))

    return boxes_xyxy


def apply_blur_to_regions(image: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
    if not boxes:
        return image

    h, w = image.shape[:2]
    output = image.copy()

    for (x1, y1, x2, y2) in boxes:
        x1, y1, x2, y2 = clamp_bbox((x1, y1, x2, y2), w, h)
        region = output[y1:y2, x1:x2]
        if region.size == 0:
            continue
        blurred = cv2.GaussianBlur(region, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
        output[y1:y2, x1:x2] = blurred

    return output


def apply_blur_to_masks(image: np.ndarray, result, target_names: List[str]) -> np.ndarray:
    """Apply Gaussian blur using instance segmentation masks for target classes.

    Falls back to returning the original image if no usable masks are present.
    """
    if not hasattr(result, "masks") or result.masks is None or not hasattr(result.masks, "data"):
        return image
    if not hasattr(result, "boxes") or result.boxes is None:
        return image

    names_map = result.names if hasattr(result, "names") else {}
    masks = result.masks.data  # [N, H, W] tensor
    boxes = result.boxes

    h, w = image.shape[:2]
    fully_blurred = cv2.GaussianBlur(image, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
    output = image.copy()

    num_instances = masks.shape[0]
    for i in range(num_instances):
        cls_idx = int(boxes.cls[i].item()) if hasattr(boxes, "cls") else None
        if cls_idx is None:
            continue
        cls_name = names_map.get(cls_idx, None)
        if cls_name is None or cls_name not in target_names:
            continue

        mask = masks[i].detach().cpu().numpy()
        mask = (mask >= 0.5).astype(np.uint8)
        if mask.sum() == 0:
            continue
        if mask.shape[0] != h or mask.shape[1] != w:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

        mask_3c = np.repeat(mask[:, :, None], 3, axis=2)
        output = np.where(mask_3c == 1, fully_blurred, output)

    return output


def process_image(input_path: str, output_path: str) -> str:
    image = read_image(input_path)
    original_h, original_w = image.shape[:2]
    work_img = image
    if UPSAMPLE_SCALE and UPSAMPLE_SCALE > 1.0:
        work_img = cv2.resize(
            image,
            (int(original_w * UPSAMPLE_SCALE), int(original_h * UPSAMPLE_SCALE)),
            interpolation=cv2.IMREAD_COLOR,
        )

    if USE_SAHI or USE_SAHI_SEG:
        if not SAHI_AVAILABLE:
            raise ImportError("SAHI not installed. Install with: pip install sahi")

        sahi_model = AutoDetectionModel.from_pretrained(
            model_path=MODEL_WEIGHTS,
            model_type="ultralytics",
            confidence_threshold=CONF_THRESHOLD,
        )

        pred = get_sliced_prediction(
            work_img,
            sahi_model,
            slice_height=SAHI_SLICE_HEIGHT,
            slice_width=SAHI_SLICE_WIDTH,
            overlap_height_ratio=SAHI_OVERLAP_RATIO,
            overlap_width_ratio=SAHI_OVERLAP_RATIO,
            verbose=0,
        )

        boxes: List[Tuple[int, int, int, int]] = []
        detected_objects = []
        for op in pred.object_prediction_list:
            cls_name = getattr(getattr(op, "category", None), "name", None)
            if not cls_name or cls_name not in SENSITIVE_CLASSES:
                continue
            x1, y1, x2, y2 = int(op.bbox.minx), int(op.bbox.miny), int(op.bbox.maxx), int(op.bbox.maxy)
            confidence = getattr(op, "score", 0.0)
            boxes.append((x1, y1, x2, y2))
            detected_objects.append((cls_name, confidence))

        print(f"SAHI found {len(boxes)} sensitive objects:")
        for obj_name, conf in detected_objects:
            print(f"  - {obj_name}: {conf:.3f}")

        if USE_SAHI_SEG:
            seg_model = load_model(MODEL_WEIGHTS)
            processed = work_img.copy()
            for (x1, y1, x2, y2) in boxes:
                x1, y1, x2, y2 = clamp_bbox((x1, y1, x2, y2), work_img.shape[1], work_img.shape[0])
                roi = processed[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                roi_results = seg_model.predict(
                    roi,
                    device=DEVICE,
                    verbose=False,
                    conf=CONF_THRESHOLD,
                    imgsz=IMG_SIZE,
                    iou=IOU_THRESHOLD,
                    augment=TTA,
                )
                roi_result = roi_results[0]
                if hasattr(roi_result, "masks") and roi_result.masks is not None and hasattr(roi_result.masks, "data"):
                    fully_blurred_roi = cv2.GaussianBlur(roi, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
                    names_map = roi_result.names if hasattr(roi_result, "names") else {}
                    masks = roi_result.masks.data
                    boxes_roi = roi_result.boxes
                    num_instances = masks.shape[0]
                    for i in range(num_instances):
                        cls_idx = int(boxes_roi.cls[i].item()) if hasattr(boxes_roi, "cls") else None
                        if cls_idx is None:
                            continue
                        cls_name = names_map.get(cls_idx, None)
                        if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                            continue
                        mask = masks[i].detach().cpu().numpy()
                        mask = (mask >= 0.5).astype(np.uint8)
                        if mask.shape[:2] != roi.shape[:2]:
                            mask = cv2.resize(mask, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
                        mask_3c = np.repeat(mask[:, :, None], 3, axis=2)
                        roi = np.where(mask_3c == 1, fully_blurred_roi, roi)
                    processed[y1:y2, x1:x2] = roi
                else:
                    blurred = cv2.GaussianBlur(roi, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
                    processed[y1:y2, x1:x2] = blurred
        else:
            processed = apply_blur_to_regions(work_img, boxes)
    else:
        model = load_model(MODEL_WEIGHTS)
        results = model.predict(work_img, device=DEVICE, conf=CONF_THRESHOLD, imgsz=IMG_SIZE, iou=IOU_THRESHOLD, augment=TTA)
        result = results[0]
        boxes = []
        detected_objects = []
        if hasattr(result, "masks") and result.masks is not None and hasattr(result.masks, "data"):
            processed = apply_blur_to_masks(work_img, result, SENSITIVE_CLASSES)
            # Extract object info from masks
            if hasattr(result, "boxes") and result.boxes is not None:
                names_map = result.names if hasattr(result, "names") else {}
                for i, box in enumerate(result.boxes):
                    cls_idx = int(box.cls.item()) if hasattr(box, "cls") else None
                    if cls_idx is None:
                        continue
                    cls_name = names_map.get(cls_idx, None)
                    if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                        continue
                    confidence = float(box.conf.item()) if hasattr(box, "conf") else 0.0
                    detected_objects.append((cls_name, confidence))
        else:
            boxes = extract_sensitive_boxes(result, SENSITIVE_CLASSES)
            processed = apply_blur_to_regions(work_img, boxes)
            # Extract object info from boxes
            if hasattr(result, "boxes") and result.boxes is not None:
                names_map = result.names if hasattr(result, "names") else {}
                for box in result.boxes:
                    cls_idx = int(box.cls.item()) if hasattr(box, "cls") else None
                    if cls_idx is None:
                        continue
                    cls_name = names_map.get(cls_idx, None)
                    if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                        continue
                    confidence = float(box.conf.item()) if hasattr(box, "conf") else 0.0
                    detected_objects.append((cls_name, confidence))

        print(f"Found {len(detected_objects)} sensitive objects:")
        for obj_name, conf in detected_objects:
            print(f"  - {obj_name}: {conf:.3f}")

    # Downscale back to original size if we upsampled
    if processed.shape[:2] != (original_h, original_w):
        processed = cv2.resize(processed, (original_w, original_h), interpolation=cv2.INTER_AREA)

    ok = cv2.imwrite(output_path, processed)
    if not ok:
        raise RuntimeError(f"Failed to write output image to '{output_path}'")
    return output_path


def process_video(input_path: str, output_path: str) -> str:
    model = load_model(MODEL_WEIGHTS)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video at '{input_path}'")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Processing video: {input_path}")
    print(f"Video info: {width}x{height} @ {fps:.1f}fps, {total_frames} frames")
    print(f"Device: {DEVICE}, Model: {MODEL_WEIGHTS}")
    if USE_SAHI or USE_SAHI_SEG:
        print(f"SAHI mode: {'segmentation' if USE_SAHI_SEG else 'box'}")
        print(f"SAHI slices: {SAHI_SLICE_WIDTH}x{SAHI_SLICE_HEIGHT}, overlap: {SAHI_OVERLAP_RATIO}")
    print(f"Confidence threshold: {CONF_THRESHOLD}, IOU: {IOU_THRESHOLD}")
    print(f"Image size: {IMG_SIZE}, Upsample: {UPSAMPLE_SCALE}")
    print("-" * 80)

    try:
        frame_count = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            frame_start = time.time()

            # Optionally upscale the frame for better small-object recall
            original_h, original_w = frame.shape[:2]
            work_frame = frame
            if UPSAMPLE_SCALE and UPSAMPLE_SCALE > 1.0:
                work_frame = cv2.resize(
                    frame,
                    (int(original_w * UPSAMPLE_SCALE), int(original_h * UPSAMPLE_SCALE)),
                    interpolation=cv2.INTER_LINEAR,
                )

            if USE_SAHI or USE_SAHI_SEG:
                if not SAHI_AVAILABLE:
                    raise ImportError("SAHI not installed. Install with: pip install sahi")
                # lazy init SAHI model once
                if 'sahi_model' not in locals():
                    print(f"Initializing SAHI model...")
                    sahi_model = AutoDetectionModel.from_pretrained(
                        model_path=MODEL_WEIGHTS,
                        model_type="ultralytics",
                        confidence_threshold=CONF_THRESHOLD,
                    )
                    print(f"SAHI model loaded successfully")

                pred = get_sliced_prediction(
                    work_frame,
                    sahi_model,
                    slice_height=SAHI_SLICE_HEIGHT,
                    slice_width=SAHI_SLICE_WIDTH,
                    overlap_height_ratio=SAHI_OVERLAP_RATIO,
                    overlap_width_ratio=SAHI_OVERLAP_RATIO,
                    verbose=0,
                )

                # Log all detected objects first (limit output to prevent spam)
                all_objects = []
                for op in pred.object_prediction_list:
                    cls_name = getattr(getattr(op, "category", None), "name", None)
                    if cls_name:
                        confidence = getattr(op, "score", 0.0)
                        # Convert to float safely
                        if hasattr(confidence, 'item'):
                            confidence = float(confidence.item())
                        elif hasattr(confidence, '__float__'):
                            confidence = float(confidence)
                        else:
                            confidence = 0.0
                        # Only log objects with reasonable confidence to reduce spam
                        if confidence > 0.1:  # Higher threshold for logging
                            all_objects.append((cls_name, confidence))

                # Limit output to prevent spam - show top 20 by confidence
                all_objects.sort(key=lambda x: x[1], reverse=True)
                display_objects = all_objects[:20]
                
                print(f"Frame {frame_count:4d}/{total_frames}: SAHI detected {len(all_objects)} objects with conf>0.1 (showing top 20):")
                for obj_name, conf in display_objects:
                    print(f"  - {obj_name}: {conf:.3f}")
                if len(all_objects) > 20:
                    print(f"  ... and {len(all_objects) - 20} more objects")

                # Filter for sensitive objects only
                boxes: List[Tuple[int, int, int, int]] = []
                detected_objects = []
                for op in pred.object_prediction_list:
                    cls_name = getattr(getattr(op, "category", None), "name", None)
                    if not cls_name or cls_name not in SENSITIVE_CLASSES:
                        continue
                    x1, y1, x2, y2 = int(op.bbox.minx), int(op.bbox.miny), int(op.bbox.maxx), int(op.bbox.maxy)
                    confidence = getattr(op, "score", 0.0)
                    # Convert to float safely
                    if hasattr(confidence, 'item'):
                        confidence = float(confidence.item())
                    elif hasattr(confidence, '__float__'):
                        confidence = float(confidence)
                    else:
                        confidence = 0.0
                    boxes.append((x1, y1, x2, y2))
                    detected_objects.append((cls_name, confidence))

                print(f"Frame {frame_count:4d}/{total_frames}: SAHI found {len(boxes)} sensitive objects:")
                for obj_name, conf in detected_objects:
                    print(f"  - {obj_name}: {conf:.3f}")

                if USE_SAHI_SEG:
                    processed = work_frame.copy()
                    for (x1, y1, x2, y2) in boxes:
                        x1, y1, x2, y2 = clamp_bbox((x1, y1, x2, y2), work_frame.shape[1], work_frame.shape[0])
                        roi = processed[y1:y2, x1:x2]
                        if roi.size == 0:
                            continue
                        roi_results = model.predict(
                            roi,
                            device=DEVICE,
                            verbose=False,
                            conf=CONF_THRESHOLD,
                            imgsz=IMG_SIZE,
                            iou=IOU_THRESHOLD,
                            augment=TTA,
                        )
                        roi_result = roi_results[0]
                        if hasattr(roi_result, "masks") and roi_result.masks is not None and hasattr(roi_result.masks, "data"):
                            fully_blurred_roi = cv2.GaussianBlur(roi, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
                            names_map = roi_result.names if hasattr(roi_result, "names") else {}
                            masks = roi_result.masks.data
                            boxes_roi = roi_result.boxes
                            num_instances = masks.shape[0]
                            for i in range(num_instances):
                                cls_idx = int(boxes_roi.cls[i].item()) if hasattr(boxes_roi, "cls") else None
                                if cls_idx is None:
                                    continue
                                cls_name = names_map.get(cls_idx, None)
                                if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                                    continue
                                mask = masks[i].detach().cpu().numpy()
                                mask = (mask >= 0.5).astype(np.uint8)
                                if mask.shape[:2] != roi.shape[:2]:
                                    mask = cv2.resize(mask, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
                                mask_3c = np.repeat(mask[:, :, None], 3, axis=2)
                                roi = np.where(mask_3c == 1, fully_blurred_roi, roi)
                            processed[y1:y2, x1:x2] = roi
                        else:
                            blurred = cv2.GaussianBlur(roi, ksize=BLUR_KERNEL, sigmaX=BLUR_SIGMA_X)
                            processed[y1:y2, x1:x2] = blurred
                else:
                    processed = apply_blur_to_regions(work_frame, boxes)
            else:
                print(f"Frame {frame_count:4d}/{total_frames}: Running single-shot detection...")
                results = model.predict(
                    work_frame,
                    device=DEVICE,
                    verbose=False,
                    conf=CONF_THRESHOLD,
                    imgsz=IMG_SIZE,
                    iou=IOU_THRESHOLD,
                    augment=TTA,
                )
                result = results[0]
                boxes = []  # Initialize boxes variable
                detected_objects = []
                if hasattr(result, "masks") and result.masks is not None and hasattr(result.masks, "data"):
                    processed = apply_blur_to_masks(work_frame, result, SENSITIVE_CLASSES)
                    # Extract object info from masks
                    if hasattr(result, "boxes") and result.boxes is not None:
                        names_map = result.names if hasattr(result, "names") else {}
                        for i, box in enumerate(result.boxes):
                            cls_idx = int(box.cls.item()) if hasattr(box, "cls") else None
                            if cls_idx is None:
                                continue
                            cls_name = names_map.get(cls_idx, None)
                            if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                                continue
                            confidence = float(box.conf.item()) if hasattr(box, "conf") else 0.0
                            detected_objects.append((cls_name, confidence))
                else:
                    boxes = extract_sensitive_boxes(result, SENSITIVE_CLASSES)
                    processed = apply_blur_to_regions(work_frame, boxes)
                    # Extract object info from boxes
                    if hasattr(result, "boxes") and result.boxes is not None:
                        names_map = result.names if hasattr(result, "names") else {}
                        for box in result.boxes:
                            cls_idx = int(box.cls.item()) if hasattr(box, "cls") else None
                            if cls_idx is None:
                                continue
                            cls_name = names_map.get(cls_idx, None)
                            if cls_name is None or cls_name not in SENSITIVE_CLASSES:
                                continue
                            confidence = float(box.conf.item()) if hasattr(box, "conf") else 0.0
                            detected_objects.append((cls_name, confidence))
                print(f"Frame {frame_count:4d}/{total_frames}: Found {len(detected_objects)} sensitive objects")
                for obj_name, conf in detected_objects:
                    print(f"  - {obj_name}: {conf:.3f}")

            # Downscale back to original frame size if we upsampled
            if processed.shape[:2] != (original_h, original_w):
                processed = cv2.resize(processed, (original_w, original_h), interpolation=cv2.INTER_AREA)

            frame_time = time.time() - frame_start
            print(f"Frame {frame_count:4d}/{total_frames}: Processed in {frame_time:.3f}s")

            out.write(processed)
    finally:
        cap.release()
        out.release()

    print(f"Video processing complete: {frame_count} frames processed")
    return output_path


def main():
    # Auto-detect by extension
    treat_as_video = is_video(INPUT_PATH)
    if treat_as_video:
        out_path = process_video(INPUT_PATH, OUTPUT_PATH)
        print(f"Saved blurred video to: {out_path}")
    else:
        out_path = process_image(INPUT_PATH, OUTPUT_PATH)
        print(f"Saved blurred image to: {out_path}")


if __name__ == "__main__":
    main()