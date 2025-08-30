from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# ------------------------------- Geometry -------------------------------- #

def iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    """
    IoU between two boxes [x1,y1,x2,y2].
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0

    area_a = max(0.0, (ax2 - ax1)) * max(0.0, (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1)) * max(0.0, (by2 - by1))
    union = area_a + area_b - inter
    if union <= 0.0:
        return 0.0
    return float(inter / union)


def inflate_and_clip(box: np.ndarray, scale_up: float, pad_px: int,
                     frame_w: int, frame_h: int) -> np.ndarray:
    """
    Inflate `box` by scale_up around its center, then add pad_px, then clip to frame.
    """
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    cx = (x1 + x2) * 0.5
    cy = (y1 + y2) * 0.5

    # scale around center
    w2 = w * scale_up
    h2 = h * scale_up
    x1s = cx - w2 / 2.0
    y1s = cy - h2 / 2.0
    x2s = cx + w2 / 2.0
    y2s = cy + h2 / 2.0

    # add pixel padding
    x1s -= pad_px
    y1s -= pad_px
    x2s += pad_px
    y2s += pad_px

    # clip
    x1s = max(0.0, x1s)
    y1s = max(0.0, y1s)
    x2s = min(float(frame_w), x2s)
    y2s = min(float(frame_h), y2s)

    # ensure valid
    if x2s <= x1s or y2s <= y1s:
        return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    return np.array([x1s, y1s, x2s, y2s], dtype=np.float32)


# ------------------------------- Tracking -------------------------------- #

@dataclass
class Track:
    track_id: int
    cls_name: str
    smooth_bbox: np.ndarray   # [x1,y1,x2,y2], smoothed
    last_bbox: np.ndarray     # latest raw detection box
    conf_avg: float
    hits: int                 # number of times matched
    misses: int               # frames since last match
    initialized: bool         # optional; keep True by default if you don't use n_init


class BoxTracker:
    """
    Lightweight detection-to-track associator with EMA smoothing.
    - Greedy IoU matching (no external deps)
    - EMA smoothing to reduce jitter
    - max_age to keep censoring when detection drops briefly
    """

    def __init__(self,
                 alpha: float = 0.5,          # EMA smoothing factor
                 iou_match_thresh: float = 0.4,
                 max_age: int = 5,            # keep track alive if missing up to this many frames
                 n_init: int = 0,             # 0 => render immediately once matched
                 scale_up: float = 1.15,      # inflate censor box by 15%
                 pad_px: int = 0):
        self.alpha = float(alpha)
        self.iou_match_thresh = float(iou_match_thresh)
        self.max_age = int(max_age)
        self.n_init = int(n_init)
        self.scale_up = float(scale_up)
        self.pad_px = int(pad_px)

        self.tracks: Dict[int, Track] = {}
        self.next_id: int = 1

    def reset(self):
        self.tracks.clear()
        self.next_id = 1

    @staticmethod
    def _ema(prev: np.ndarray, cur: np.ndarray, alpha: float) -> np.ndarray:
        if prev is None:
            return cur.copy()
        return alpha * cur + (1.0 - alpha) * prev

    def _greedy_match(self,
                      det_boxes: List[np.ndarray],
                      det_names: List[str],
                      frame_wh: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Greedy IoU matching per class:
        Returns (matches, unmatched_track_ids, unmatched_det_idxs)
        where matches is list of (track_id, det_index).
        """
        # build candidate pairs (same class, IoU >= thresh)
        pairs = []  # (IoU, track_id, det_idx)
        for tid, tr in self.tracks.items():
            for j, (db, cname) in enumerate(zip(det_boxes, det_names)):
                if tr.cls_name != cname:
                    continue
                iou = iou_xyxy(tr.last_bbox, db)
                if iou >= self.iou_match_thresh:
                    pairs.append((iou, tid, j))

        # sort by best IoU first
        pairs.sort(reverse=True, key=lambda x: x[0])

        matched_tracks = set()
        matched_dets = set()
        matches: List[Tuple[int, int]] = []
        for iou, tid, j in pairs:
            if tid in matched_tracks or j in matched_dets:
                continue
            matched_tracks.add(tid)
            matched_dets.add(j)
            matches.append((tid, j))

        # compute unmatched sets
        unmatched_track_ids = [tid for tid in self.tracks.keys() if tid not in matched_tracks]
        unmatched_det_idxs = [j for j in range(len(det_boxes)) if j not in matched_dets]
        return matches, unmatched_track_ids, unmatched_det_idxs

    def step(self,
             detections: List[Dict[str, Any]],
             frame_size: Tuple[int, int]) -> List[Track]:
        """
        Update tracker with current frame detections and return ACTIVE tracks
        for censoring this frame.
        `detections` expects dicts with keys: "xyxy": list[4], "conf": float, "name": str
        """
        W, H = frame_size
        # 1) Prepare det arrays
        det_boxes: List[np.ndarray] = []
        det_names: List[str] = []
        det_confs: List[float] = []
        for d in detections:
            b = np.array(d["xyxy"], dtype=np.float32)
            # enforce valid box
            if b[2] <= b[0] or b[3] <= b[1]:
                continue
            det_boxes.append(b)
            det_names.append(str(d["name"]))
            det_confs.append(float(d["conf"]))

        # 2) Match to existing tracks
        matches, unmatched_track_ids, unmatched_det_idxs = self._greedy_match(det_boxes, det_names, (W, H))

        # 3) Update matched tracks
        for tid, j in matches:
            tr = self.tracks[tid]
            det_box = det_boxes[j]
            det_conf = det_confs[j]
            tr.last_bbox = det_box
            tr.smooth_bbox = self._ema(tr.smooth_bbox, det_box, self.alpha)
            tr.conf_avg = 0.7 * tr.conf_avg + 0.3 * det_conf if tr.hits > 0 else det_conf
            tr.hits += 1
            tr.misses = 0
            if tr.hits >= self.n_init:
                tr.initialized = True

        # 4) Age unmatched tracks
        to_delete = []
        for tid in unmatched_track_ids:
            tr = self.tracks[tid]
            tr.misses += 1
            # keep smooth box as-is during misses (temporal persistence)
            if tr.misses > self.max_age:
                to_delete.append(tid)
        for tid in to_delete:
            self.tracks.pop(tid, None)

        # 5) Create new tracks for unmatched detections
        for j in unmatched_det_idxs:
            det_box = det_boxes[j]
            cname = det_names[j]
            det_conf = det_confs[j]
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = Track(
                track_id=tid,
                cls_name=cname,
                smooth_bbox=det_box.copy(),   # initialize smoothed at first box
                last_bbox=det_box.copy(),
                conf_avg=det_conf,
                hits=1,
                misses=0,
                initialized=(self.n_init <= 1),
            )

        # 6) Collect active tracks for rendering this frame
        active: List[Track] = []
        for tr in self.tracks.values():
            if tr.initialized and tr.misses <= self.max_age:
                # ensure box is valid and within frame after inflate/pad
                inf_box = inflate_and_clip(tr.smooth_bbox, self.scale_up, self.pad_px, W, H)
                if inf_box[2] > inf_box[0] and inf_box[3] > inf_box[1]:
                    # update smooth box to clipped inflated version for rendering
                    # (keeps final region stable in subsequent frames too)
                    tr.smooth_bbox = inf_box
                    active.append(tr)

        return active