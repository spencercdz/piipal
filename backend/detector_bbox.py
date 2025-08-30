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
    "numeric":     re.compile(r"\b\d{4,}\b")
}

PATTERNS_FUZZY = {
    "credit_card": re.compile(
        r"\b(?:(?:\d{4}[-\s]?){3}\d{4}){e<=2}\b"
    ),

    "email": re.compile(
        # allow up to 2 total insertions/deletions/subs
        r"(?:(?:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})){e<=2}"
    ),

    "phone": re.compile(
        # one error in country code / separators / digits
        r"(?:(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?){1,4}\d{1,4}){e<=1}"
    ),

    "nric_fin": re.compile(
        # 9 chars total, allow 1 mis-read
        r"\b(?:[STFG]\d{7}[A-Z]){e<=1}\b",
        regex.IGNORECASE
    ),

    "uen": re.compile(
        # 9–10 chars, allow 1 error
        r"\b(?:(?:\d{9}|\d{8}[A-Z]|[STFG]\d{7}[A-Z])){e<=1}\b",
        regex.IGNORECASE
    ),

    "sg_phone": re.compile(
        # 8 digits or +65 prefix, allow 1 error
        r"\b(?:(?:\+65[-.\s]?)?[3698]\d{3}[-.\s]?\d{4}){e<=1}\b"
    ),

    "sg_postal": re.compile(
        # 6 digits, allow 1 error
        r"\b(?:\d{6}){e<=1}\b"
    ),

    "passport": re.compile(
        # 6–9 chars, allow 1 error
        r"\b(?:[A-Z]{1,2}\d{5,7}){e<=1}\b",
        regex.IGNORECASE
    ),

    "iban": re.compile(
        # 15–34 chars, allow up to 2 errors
        r"\b(?:[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}){e<=2}\b"
    ),

    "swift": re.compile(
        # 8 or 11 chars, allow 1 error
        r"\b(?:[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?){e<=1}\b"
    ),

    "ipv4": re.compile(
        # ~15 chars, allow 1 error in octets or dots
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\."
        r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\."
        r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\."
        r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)){e<=1}\b"
    ),

    "ipv6": re.compile(
        # allow 2 errors in hex groups or colons
        r"\b(?:(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}){e<=2}\b",
        regex.IGNORECASE
    ),

    "mac_address": re.compile(
        # ~17 chars, allow 2 errors in hex or separators
        r"\b(?:(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}){e<=2}\b",
        regex.IGNORECASE
    ),

    "uuid": re.compile(
        # 36 chars with hyphens, allow 3 errors
        r"\b(?:[0-9a-fA-F]{8}\-(?:[0-9a-fA-F]{4}\-){3}[0-9a-fA-F]{12}){e<=3}\b"
    ),

    "vin": re.compile(
        # 17 alnum, allow 2 errors
        r"\b(?:[A-HJ-NPR-Z0-9]{17}){e<=2}\b"
    ),
    "alphanum":    re.compile(r"(?=\w*\d)(?=\w*[A-Za-z])[A-Za-z0-9]{3,}"),
    "numeric":     re.compile(r"\b\d{4,}\b"),
}

import numpy as np
import torch

def looks_sensitive(text, nlp=False):
    """
    Returns the PII class label if `text` is sensitive, otherwise None.
    """
    if nlp:
        # all labels except the 'O' (non‐PII) tag
        sensitive_labels = set(model.config.id2label.values()) - {'O'}

        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        preds = torch.argmax(outputs.logits, dim=-1)[0]
        for label_id in preds:
            if label_id.item() != model.config.label2id['O']:
                label_name = model.config.id2label[label_id.item()]
                if label_name in sensitive_labels:
                    print(f"PII NLP Model detected '{text}' as {label_name}")
                    return label_name

        return None

    else:
        t = text.strip()
        if not t:
            return None

        # PATTERNS: {"EMAIL": re.compile(...), "PHONE": re.compile(...), …}
        for label, pat in PATTERNS_FUZZY.items():
            if pat.search(t):
                print(f"REGEX detected: '{text}' as {label}")
                return label

        return None


class PiiTracker:
    def __init__(self, max_lost=8, iou_thresh=0.3):
        self.max_lost = max_lost
        self.iou_thresh = iou_thresh
        self.tracks = {}
        self.next_id = 0

    def update(self, detections):
        """
        detections: list of ((x,y,w,h), cls)
        """
        new_tracks = {}
        used = set()

        # 1) Match incoming detections to existing tracks
        for det_bbox, det_cls in detections:
            best_id, best_iou = None, 0.0
            for tid, data in self.tracks.items():
                iou = compute_iou(det_bbox, data['bbox'])
                if iou > best_iou:
                    best_id, best_iou = tid, iou

            if best_iou >= self.iou_thresh:
                # update existing track
                new_tracks[best_id] = {
                    'bbox': det_bbox,
                    'class': det_cls,
                    'lost': 0
                }
                used.add(best_id)
            else:
                # start a fresh track
                new_tracks[self.next_id] = {
                    'bbox': det_bbox,
                    'class': det_cls,
                    'lost': 0
                }
                self.next_id += 1

        # 2) Age out tracks not matched this frame
        for tid, data in self.tracks.items():
            if tid not in used:
                data['lost'] += 1
                if data['lost'] <= self.max_lost:
                    new_tracks[tid] = data

        self.tracks = new_tracks

    def active(self):
        """
        Returns list of (bbox, cls) for current tracks.
        """
        return [(d['bbox'], d['class']) for d in self.tracks.values()]


def censor_frame_consistent_bbox(
    frame,
    reader,
    tracker,
    pad=8,
    min_prob=0.2,
    ocr_params=None,
    nlp=False
):
    """
    Returns a dict for this frame:
      { "EMAIL": [[x,y,w,h], …],
        "PHONE": [[…], …], … }
    """
    if ocr_params is None:
        ocr_params = {
            "text_threshold": 0.5,
            "low_text": 0.6,
            "add_margin": 0.2,
            "contrast_ths": 0.1,
            "adjust_contrast": 0.5
        }

    H, W = frame.shape[:2]
    frame_output = {}

    # 1) OCR → raw detections
    results = reader.readtext(frame, detail=1, paragraph=False, **ocr_params)

    dets = []
    for bbox_pts, text, prob in results:
        if prob < min_prob:
            continue

        cls = looks_sensitive(text, nlp)
        if cls is None:
            continue

        pts = np.array(bbox_pts).astype(int)
        x1, y1 = pts[:,0].min(), pts[:,1].min()
        x2, y2 = pts[:,0].max(), pts[:,1].max()

        x = max(0, x1 - pad)
        y = max(0, y1 - pad)
        w = min(W, x2 + pad) - x
        h = min(H, y2 + pad) - y

        dets.append(((x, y, w, h), cls))

    # 2) Smooth & persist across frames
    tracker.update(dets)

    # 3) Collect active tracks into per‐class lists
    for (x, y, w, h), cls in tracker.active():
        frame_output.setdefault(cls, []).append([x, y, w, h])

    return frame_output

# 2) Simple IoU
def compute_iou(a, b):
    xA = max(a[0], b[0]); yA = max(a[1], b[1])
    xB = min(a[0]+a[2], b[0]+b[2]); yB = min(a[1]+a[3], b[1]+b[3])
    if xB <= xA or yB <= yA:
        return 0.0
    inter = (xB - xA) * (yB - yA)
    return inter / float(a[2]*a[3] + b[2]*b[3] - inter)

# 4) Redaction helpers
def pixelate(roi, blocks=8):
    h, w = roi.shape[:2]
    small = cv2.resize(roi, (blocks, blocks), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

def blackout(roi):
    return np.zeros_like(roi)

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
