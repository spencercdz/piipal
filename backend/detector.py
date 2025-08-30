import cv2
import numpy as np
import easyocr
import re
import torch

# Load OCR model
print("Loading EasyOCR model...")
reader = easyocr.Reader(["en"], gpu=True)
print("EasyOCR model loaded successfully")

# 1) REGEX patterns for PII detection
PATTERNS = {
    "credit_card": re.compile(r"(?:\d{4}[-\s]?){3}\d{4}"),
    "email":       re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone":       re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?){1,4}\d{1,4}"),
    "alphanum":    re.compile(r"(?=\w*\d)(?=\w*[A-Za-z])[A-Za-z0-9]{3,}"),
    "numeric":     re.compile(r"\b\d{4,}\b"),
    "ssn":         re.compile(r"\d{3}-\d{2}-\d{4}"),
    "date":        re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"),
    "address":     re.compile(r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)"),
}
<<<<<<< HEAD
def looks_sensitive(text, nlp=False):
    if nlp:
        # Default to all non-O labels for now
        sensitive_labels = set(model.config.id2label.values()) - {'O'}
        
        # Tokenize input text
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Get the model predictions
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get the predicted labels
        predictions = torch.argmax(outputs.logits, dim=-1)
        
        # Check if any specified sensitive labels exist
        for prediction in predictions[0]:
            label_id = prediction.item()
            if label_id != model.config.label2id['O']:
                label_name = model.config.id2label[label_id]
                if label_name in sensitive_labels:
                    print(f"PII NLP Model detected '{text}' as {label_name}")
                    return True
        
        return False

    else:
        t = text.strip()
        if not t:
            return False
        for pat in PATTERNS.values():
            if pat.search(t):
                print(f"REGEX detected: '{text}' as {pat}")
                return True
# 2) Simple IoU
def compute_iou(a, b):
    xA = max(a[0], b[0]); yA = max(a[1], b[1])
    xB = min(a[0]+a[2], b[0]+b[2]); yB = min(a[1]+a[3], b[1]+b[3])
    if xB <= xA or yB <= yA:
        return 0.0
    inter = (xB - xA) * (yB - yA)
    return inter / float(a[2]*a[3] + b[2]*b[3] - inter)

# 3) Tracker for persistent redaction
class PiiTracker:
    def __init__(self, max_lost=8, iou_thresh=0.3):
        self.max_lost = max_lost
        self.iou_thresh = iou_thresh
        self.tracks = {}
        self.next_id = 0

    def update(self, detections):
        """
        detections: list of ((x,y,w,h), text)
        """
        new_tracks = {}
        used = set()

        # 3.1 Match detections to existing tracks
        for det_bbox, det_text in detections:
            best_id, best_iou = None, 0.0
            for tid, data in self.tracks.items():
                iou = compute_iou(det_bbox, data['bbox'])
                if iou > best_iou:
                    best_id, best_iou = tid, iou
            if best_iou >= self.iou_thresh:
                # update existing track
                new_tracks[best_id] = {
                    'bbox': det_bbox,
                    'text': det_text,
                    'lost': 0
                }
                used.add(best_id)
            else:
                # start a fresh track
                new_tracks[self.next_id] = {
                    'bbox': det_bbox,
                    'text': det_text,
                    'lost': 0
                }
                self.next_id += 1

        # 3.2 Age out tracks not matched this frame
        for tid, data in self.tracks.items():
            if tid not in used:
                data['lost'] += 1
                if data['lost'] <= self.max_lost:
                    new_tracks[tid] = data

        self.tracks = new_tracks

    def active(self):
        """Return list of (bbox, text) for current tracks."""
        return [(d['bbox'], d['text']) for d in self.tracks.values()]

# 4) Redaction helpers
def pixelate(roi, blocks=8):
    h, w = roi.shape[:2]
    small = cv2.resize(roi, (blocks, blocks), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

def blackout(roi):
    return np.zeros_like(roi)

# 5) Frame‐level censoring with persistence
def censor_frame_consistent(
    frame,
    reader,
    tracker,
    pad=8,
    min_prob=0.2,
    redaction_mode="pixelate",
    blur_ksize=(51,51),
    ocr_params={"text_threshold": 0.5, "low_text": 0.6, "add_margin": 0.2, "contrast_ths": 0.1, "adjust_contrast": 0.5},
    debug=False,
    nlp=False
):
    """
    1) OCR→detect sensitive bboxes
    2) tracker.update() to smooth over missing frames
    3) redact all active tracks each frame
    4) debug overlays if requested
    """
    H, W = frame.shape[:2]

    print(f"Starting OCR on frame {frame.shape}")

    # 5.1 Detect PII boxes this frame
    dets = []
    results = reader.readtext(frame, detail=1, paragraph=False, **ocr_params)
    print(f"OCR completed, found {len(results)} text regions")

    for bbox_pts, text, prob in results:
        if prob < min_prob:
            continue
        if not looks_sensitive(text, nlp):
            continue

        pts = np.array(bbox_pts).astype(int)
        x1, y1 = pts[:,0].min(), pts[:,1].min()
        x2, y2 = pts[:,0].max(), pts[:,1].max()
        # pad region
        x = max(0, x1-pad); y = max(0, y1-pad)
        w = min(W, x2+pad) - x;  h = min(H, y2+pad) - y

        print(f"SENSITIVE detected: '{text}' at bbox ({x},{y},{w},{h})")
        dets.append(((x, y, w, h), text))

    # 5.2 Update tracker
    tracker.update(dets)
    print(f"Updating tracker with {len(dets)} sensitive detections...")

    # 5.3 Redact all active tracks
    out = frame.copy()
    print(f"Applying {redaction_mode} redaction to active tracks...")
    for (x,y,w,h), text in tracker.active():
        roi = out[y:y+h, x:x+w]

        if redaction_mode == "blur":
            out[y:y+h, x:x+w] = cv2.GaussianBlur(roi, blur_ksize, 0)
        elif redaction_mode == "pixelate":
            out[y:y+h, x:x+w] = pixelate(roi)
        else:  # blackout
            out[y:y+h, x:x+w] = blackout(roi)

    if debug:
      for bbox_pts, text, prob in results:
          if prob < 0.3:
              continue

          pts = np.array(bbox_pts).astype(int)
          x1, y1 = pts[:,0].min(), pts[:,1].min()
          x2, y2 = pts[:,0].max(), pts[:,1].max()
          x = max(0, x1-pad); y = max(0, y1-pad)
          w = min(W, x2+pad) - x;  h = min(H, y2+pad) - y
          sus = looks_sensitive(text, nlp)
          cv2.polylines(out, [pts], isClosed=True, color=(0,0,255) if sus else (0,255,0), thickness=2)
          cv2.putText(out, text, (x1, max(15,y1-5)),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255) if sus else (0,255,0), 1)
    return out

# 6) Video loop
def process_video_consistent(
    input_path,
    output_path="consistent_censor.mp4",
    pad=8,
    min_prob=0.2,
    max_lost=8, iou_thresh=0.3,
    redaction_mode="blackout",
    ocr_params={"text_threshold": 0.5, "low_text": 0.6, "add_margin": 0.2, "contrast_ths": 0.1, "adjust_contrast": 0.5},
    debug=False,
    nlp=False
):
    print(f"Starting video processing...")
    print(f"Tracker: max_lost={max_lost}, iou_thresh={iou_thresh}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Settings: pad={pad}, min_prob={min_prob}, redaction_mode={redaction_mode}")

    cap     = cv2.VideoCapture(input_path)
    fourcc  = cv2.VideoWriter_fourcc(*"mp4v")
    fps     = cap.get(cv2.CAP_PROP_FPS) or 20.0
    W       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer  = cv2.VideoWriter(output_path, fourcc, fps, (W, H))

    tracker = PiiTracker(max_lost=max_lost, iou_thresh=iou_thresh)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        out = censor_frame_consistent(
            frame, reader, tracker,
            pad=pad,
            min_prob=min_prob,
            redaction_mode=redaction_mode,
            blur_ksize=(51,51),
            ocr_params=ocr_params,
            debug=debug,
            nlp=nlp
        )
        writer.write(out)
    
    print(f"Video processing completed!")

    cap.release()
    writer.release()
    print(f"Output saved to: {output_path}")

    return output_path

# 7) Usage example (commented out to avoid running on import)
# out_vid = process_video_consistent(
#     "data/car_vid.mp4",
#     output_path="data/car_vid_blurred.mp4",
#     pad=0,
#     min_prob=0.1,
#     max_lost=15, iou_thresh=0.2,
#     redaction_mode="pixelate",
#     ocr_params={"text_threshold": 0.3, "low_text": 0.6, "add_margin": 0.2, "contrast_ths":0.1, "adjust_contrast":0.5},
#     debug=False
# )