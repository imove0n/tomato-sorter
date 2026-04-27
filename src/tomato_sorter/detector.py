"""Camera capture + YOLO inference (ultralytics PT) in a background thread.

NOTE: We tried NCNN export but the PNNX-based conversion produces a model
that returns 0.7% confidences (broken). The original .pt model works perfectly
(96%+ confidence). Switched back to .pt + ultralytics for reliability.
"""
import threading
import time
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO

from .config import PROJECT_ROOT, SETTINGS


class Detection:
    __slots__ = ("class_id", "label", "conf", "box")

    def __init__(self, class_id: int, label: str, conf: float, box: tuple):
        self.class_id = class_id
        self.label = label
        self.conf = conf
        self.box = box      # (x1, y1, x2, y2) on the original camera frame

    def to_dict(self):
        return {"class_id": self.class_id, "label": self.label,
                "conf": round(self.conf, 3), "box": list(self.box)}


_CLASS_COLORS = {
    "ripe":   (0, 220, 60),    # green
    "unripe": (0, 140, 255),   # orange
    "rotten": (0, 0, 220),     # red
}


class Detector:
    def __init__(self):
        cfg_cam  = SETTINGS["camera"]
        cfg_det  = SETTINGS["detector"]
        self.cam_w        = cfg_cam["width"]
        self.cam_h        = cfg_cam["height"]
        self.cam_device   = cfg_cam["device"]
        self.input_size   = cfg_det["input_size"]
        self.conf_thresh  = cfg_det["conf_threshold"]
        self.iou_thresh   = cfg_det["iou_threshold"]
        self.classes      = cfg_det["classes"]

        # Load ultralytics .pt model (works reliably, NCNN export was broken)
        pt_path = PROJECT_ROOT / "models" / "my_model11n480" / "train" / "weights" / "best.pt"
        self._model = YOLO(str(pt_path))

        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None    # annotated BGR
        self._latest_detections: list[Detection] = []
        self._latest_jpeg: Optional[bytes] = None
        self._fps = 0.0
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _open_camera(self):
        """Try the configured device first, then probe video0..video4."""
        candidates = [self.cam_device] + [i for i in range(5) if i != self.cam_device]
        for idx in candidates:
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.cam_w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"[detector] Using /dev/video{idx}")
                    return cap
                cap.release()
        raise RuntimeError("No working USB camera found")

    def start(self):
        self._cap = self._open_camera()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()

    def _detect(self, frame) -> list[Detection]:
        results = self._model(frame, conf=self.conf_thresh,
                              iou=self.iou_thresh, imgsz=self.input_size,
                              verbose=False)
        out = []
        for r in results:
            for box in r.boxes:
                cid = int(box.cls[0])
                label = self.classes[cid] if cid < len(self.classes) else f"cls{cid}"
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                out.append(Detection(cid, label, conf,
                                     (int(x1), int(y1), int(x2), int(y2))))
        return out

    def _annotate(self, frame, detections):
        for d in detections:
            color = _CLASS_COLORS.get(d.label, (200, 200, 200))
            x1, y1, x2, y2 = d.box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = f"{d.label} {d.conf:.2f}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(frame, text, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(frame, f"FPS: {self._fps:.1f}", (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        return frame

    def _loop(self):
        last_t = time.time()
        n = 0
        while self._running:
            if self._cap is None:
                time.sleep(0.05)
                continue
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.05)
                continue

            dets = self._detect(frame)

            with self._lock:
                self._latest_detections = dets
                self._latest_frame = frame   # keep raw frame, no annotation in hot loop

            n += 1
            now = time.time()
            if now - last_t >= 1.0:
                self._fps = n / (now - last_t)
                n = 0
                last_t = now

    # ----- public read accessors -----
    def latest_detections(self) -> list[dict]:
        with self._lock:
            return [d.to_dict() for d in self._latest_detections]

    def latest_jpeg(self) -> Optional[bytes]:
        """On-demand: encode latest frame with annotations only when requested."""
        with self._lock:
            frame = self._latest_frame
            dets  = list(self._latest_detections)
        if frame is None:
            return None
        annotated = self._annotate(frame.copy(), dets)
        ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buf.tobytes() if ok else None

    def fps(self) -> float:
        return self._fps

    def best_detection(self) -> Optional[Detection]:
        """Return the highest-confidence detection in the current frame."""
        with self._lock:
            if not self._latest_detections:
                return None
            return max(self._latest_detections, key=lambda d: d.conf)
