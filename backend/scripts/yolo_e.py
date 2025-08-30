from ultralytics import YOLOE
from pathlib import Path
import cv2
import glob
import os
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from moviepy.editor import VideoFileClip

model = YOLOE('yoloe-11l-seg.pt')

names = ["traffic sign", 
         "parking sign",
         "road sign",
         "sign",
         "license plate",
         "signage",
         "billboard",
         "face",
         "tattoo",
         "birthmark",
         "building",
         "badge",
         "identity card",
         "credit card",
         "computer screen",
         "phone",
         "document",
         "package label",
         "calendar",
         "planner",
         "mirror",
         "ticket"
         ]
model.set_classes(names, model.get_text_pe(names))

HD_CANDIDATE_FRAME_DIR = "backend/data/hd_candidate_frames"
CANDIDATE_FRAME_DIR = "backend/data/candidate_frames"

HD_CANDIDATE_FRAME_OUT_DIR = "backend/data/hd_candidate_frames/output"
CANDIDATE_FRAME_OUT_DIR = "backend/data/candidate_frames/output"

def get_candidate_frame_paths(isHD) -> Tuple[List[str], str]:
    if isHD:
        return glob.glob(os.path.join(HD_CANDIDATE_FRAME_DIR, "*.jpg")), HD_CANDIDATE_FRAME_OUT_DIR
    else:
        return glob.glob(os.path.join(CANDIDATE_FRAME_DIR, "*.jpg")), CANDIDATE_FRAME_OUT_DIR
    

def run_image(
    model,
    img_path: str,
    outdir: str,
    imgsz: int = 640,
    conf: float = 0.25,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Run YOLOE inference on a single image, annotate, and save to outdir.

    Args:
        model: Ultralytics YOLOE model (already loaded + set_classes if needed).
        img_path: Path to input image.
        outdir: Directory to save the annotated image.
        imgsz: Inference image size.
        conf: Confidence threshold.
        verbose: Ultralytics predict verbosity.

    Returns:
        dets: List of detections with keys: xyxy, conf, cls, name.
    """
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)

    # Read image with cv2
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image at {img_path}")

    # Inference
    results = model.predict(source=img, imgsz=imgsz, conf=conf, verbose=verbose)
    r = results[0]

    dets: List[Dict[str, Any]] = []
    if r.boxes is not None and len(r.boxes) > 0:
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        clss = r.boxes.cls.cpu().numpy().astype(int)
        for box, c, k in zip(xyxy, confs, clss):
            dets.append({
                "xyxy": box.tolist(),
                "conf": float(c),
                "cls": int(k),
                "name": r.names.get(int(k), str(int(k))),  # r.names is dict
            })

    # Annotate
    annotated = r.plot()

    # Save annotated image with "_output" suffix
    in_path = Path(img_path)
    out_file = Path(outdir) / f"{in_path.stem}_output{in_path.suffix}"
    ok = cv2.imwrite(str(out_file), annotated)
    if not ok:
        raise IOError(f"Failed to write annotated image to {out_file}")
    else: print(f"Wrote blurred image to {out_file}")

    return dets

def apply_pixelation(img, xi1, yi1, xi2, yi2, pixel_size: int = 10):
    """
    Apply pixelation (mosaic) to the region [yi1:yi2, xi1:xi2] of img.
    
    Args:
        img: BGR numpy array
        xi1, yi1, xi2, yi2: coordinates of the box
        pixel_size: smaller -> finer detail, larger -> more censoring
    """
    roi = img[yi1:yi2, xi1:xi2]

    h, w = roi.shape[:2]
    if h == 0 or w == 0:
        return img  # skip invalid boxes

    # Downscale to (w//pixel_size, h//pixel_size)
    temp = cv2.resize(roi, (max(1, w // pixel_size), max(1, h // pixel_size)), interpolation=cv2.INTER_LINEAR)

    # Upscale back to original ROI size with nearest-neighbor → blocky look
    pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

    # Replace region in original image
    img[yi1:yi2, xi1:xi2] = pixelated
    return img


def run_image_pixelate(
    model,
    img_path: str,
    outdir: str,
    imgsz: int = 640,
    conf: float = 0.25,
    verbose: bool = False,
    kernel: Tuple[int, int] | None = None,   # e.g., (99, 99) for very strong blur
    sigmaX: float = 0,                        # 0 lets OpenCV choose based on kernel
    padding_px: int = 0  ,                     # optional padding around each box
    save: bool = True,
    pixel_size: int = 10,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Run YOLOE inference on an image, blur the regions inside each bounding box,
    and save to `outdir` with the same name + '_output' suffix.

    Args:
        model:    Ultralytics YOLOE model (already loaded and set_classes if needed).
        img_path: Path to input image.
        outdir:   Directory to save the blurred image.
        imgsz:    Inference image size.
        conf:     Confidence threshold.
        verbose:  Ultralytics predict verbosity.
        kernel:   Optional fixed Gaussian kernel (odd, odd). If None -> auto per box.
        sigmaX:   Gaussian sigmaX (0 -> computed from kernel).
        padding_px: Extra pixels to expand each bbox on all sides (clipped to image bounds).

    Returns:
        dets: List of detections with fields: xyxy, conf, cls, name.
    """
    outdir_p = Path(outdir)
    outdir_p.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image at {img_path}")

    # Inference on the already-loaded NumPy image
    results = model.predict(source=img, imgsz=imgsz, conf=conf, verbose=verbose)
    r = results[0]

    # Prepare detections list
    dets: List[Dict[str, Any]] = []
    H, W = img.shape[:2]
    out_img = img.copy()

    if r.boxes is not None and len(r.boxes) > 0:
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        clss  = r.boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), c, k in zip(xyxy, confs, clss):
            # Clip + pad bbox
            xi1 = max(0, int(np.floor(x1)) - padding_px)
            yi1 = max(0, int(np.floor(y1)) - padding_px)
            xi2 = min(W, int(np.ceil(x2)) + padding_px)
            yi2 = min(H, int(np.ceil(y2)) + padding_px)
            
            if xi2 - xi1 > 1 and yi2 - yi1 > 1:
                out_img = apply_pixelation(out_img, xi1, yi1, xi2, yi2, pixel_size=pixel_size)


            dets.append({
                "xyxy": [float(x1), float(y1), float(x2), float(y2)],
                "conf": float(c),
                "cls":  int(k),
                "name": r.names.get(int(k), str(int(k))),  # r.names is a dict
            })

    # Save output with "_output" suffix
    if save:
        in_path = Path(img_path)
        out_file = outdir_p / f"{in_path.stem}_output{in_path.suffix}"
        ok = cv2.imwrite(str(out_file), out_img)
        if not ok:
            raise IOError(f"Failed to write blurred image to {out_file}")
        else: print(f"Wrote blurred image to {out_file}")

    return out_img, dets

def _pixelate_frame_with_yoloe(
    model,
    frame_bgr: np.ndarray,
    imgsz: int = 640,
    conf: float = 0.25,
    verbose: bool = False,
    padding_px: int = 0,
    pixel_size: int = 12,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Frame-level variant: runs YOLOE on a BGR frame and pixelates every detected region.
    Detection set is already constrained by model.set_classes(...).
    """
    H, W = frame_bgr.shape[:2]
    out_img = frame_bgr.copy()

    results = model.predict(source=out_img, imgsz=imgsz, conf=conf, verbose=verbose)
    r = results[0]

    dets: List[Dict[str, Any]] = []
    if r.boxes is not None and len(r.boxes) > 0:
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        clss  = r.boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), c, k in zip(xyxy, confs, clss):
            # no extra filtering; you already constrained classes via set_classes
            xi1 = max(0, int(np.floor(x1)) - padding_px)
            yi1 = max(0, int(np.floor(y1)) - padding_px)
            xi2 = min(W, int(np.ceil(x2))  + padding_px)
            yi2 = min(H, int(np.ceil(y2))  + padding_px)

            if xi2 - xi1 > 1 and yi2 - yi1 > 1:
                out_img = apply_pixelation(out_img, xi1, yi1, xi2, yi2, pixel_size=pixel_size)

            dets.append({
                "xyxy": [float(x1), float(y1), float(x2), float(y2)],
                "conf": float(c),
                "cls":  int(k),
                "name": r.names.get(int(k), str(int(k))),  # r.names is dict in your setup
            })

    return out_img, dets

def run_video_censor(
    model,
    in_video_path: str = "/backend/data/HD_car_vid.mp4",
    out_video_path: str = "/backend/data/HD_car_vid_pixelated_medium.mp4",
    imgsz: int = 640,
    conf: float = 0.25,
    padding_px: int = 0,
    pixel_size: int = 14,
    verbose: bool = False
) -> None:
    """
    1) Read MP4 from /backend/data/HD_car_vid.mp4 (by default)
    2) Extract original audio
    3) For each frame, run YOLOE and pixelate detected regions (no per-frame saves)
    4) Write processed video to /backend/data/HD_car_vid_pixelated.mp4 with original audio
    """
    in_path = Path(in_video_path)
    out_path = Path(out_video_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    clip = VideoFileClip(str(in_path))
    fps = clip.fps
    width, height = clip.size  # (w, h)
    audio = clip.audio  # may be None

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # widely compatible; 'avc1' may also work
    tmp_silent_path = out_path.with_suffix(".video_silent.mp4")
    writer = cv2.VideoWriter(str(tmp_silent_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        clip.close()
        raise RuntimeError("Failed to open VideoWriter for output video stream.")

    # Iterate frames in RGB from moviepy, convert to BGR for OpenCV and model
    frame_num = int(clip.duration * fps)
    frame_count = 0
    print(f"Processing {frame_num} frames at {fps} FPS, resolution {width}x{height}")
    for frame_rgb in clip.iter_frames(fps=fps, dtype="uint8"):
        frame_count += 1
        if frame_count % 50 == 0 or frame_count == frame_num:
            print(f"  Processing frame {frame_count}/{frame_num}...")
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        processed_bgr, _ = _pixelate_frame_with_yoloe(
            model,
            frame_bgr,
            imgsz=imgsz,
            conf=conf,
            verbose=verbose,
            padding_px=padding_px,
            pixel_size=pixel_size,
        )

        writer.write(processed_bgr)

    writer.release()

    # Mux original audio back
    processed_clip = VideoFileClip(str(tmp_silent_path))
    if audio is not None:
        processed_clip = processed_clip.set_audio(audio)

    processed_clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac" if audio is not None else None,
        fps=fps,
        threads=4,
        verbose=False,
        logger=None
    )
    processed_clip.close()
    clip.close()

    # Clean up temp file
    try:
        Path(tmp_silent_path).unlink()
    except Exception:
        pass

def main():
    # frame_paths, outdir = get_candidate_frame_paths(isHD=True)
    # for path in frame_paths:
    #     print(f"Processing {path}")
    #     img = cv2.imread(path)
    #     if img is None:
    #         print(f"Could not read image at '{path}'")
    #     else:
    #         output_image, dets = run_image_pixelate(model, path, outdir, imgsz=640, conf=0.2, verbose=False)
    #         print(f"Detections: {dets}")
    
    run_video_censor(
        model,
        in_video_path="./backend/data/HD_car_vid.MP4",
        out_video_path="./backend/data/HD_car_vid_pixelated.mp4",
        imgsz=640,
        conf=0.15,
        padding_px=2,   # small margin around boxes
        pixel_size=16,  # increase for stronger pixelation
        verbose=False
    )
    
if __name__ == "__main__":
    main()
