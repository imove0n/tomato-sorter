#!/usr/bin/env python3
"""
Camera + NCNN inference smoke test — MJPEG stream edition.
Open http://localhost:8080 in Chromium on the Pi to see the live feed.
Press Ctrl+C to stop.

Run from project root:
    .venv/bin/python scripts/test_camera.py
"""
import io
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import cv2
import ncnn
import numpy as np

MODEL_PARAM = "models/best.ncnn.param"
MODEL_BIN   = "models/best.ncnn.bin"
INPUT_SIZE  = 480
CONF_THRESH = 0.4
IOU_THRESH  = 0.45
CLASSES     = ["ripe", "rotten", "unripe"]
COLORS      = [(0, 220, 60), (0, 0, 220), (0, 140, 255)]  # green, red, orange

# Shared state between capture thread and HTTP server
_frame_lock  = threading.Lock()
_latest_jpeg = None
_stats       = {"fps": 0.0, "detections": 0, "output_shape": "?"}


def preprocess(frame: np.ndarray) -> np.ndarray:
    img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = img.transpose(2, 0, 1)
    return img


def postprocess(raw: np.ndarray, orig_w: int, orig_h: int) -> list:
    preds = raw.T
    num_classes = preds.shape[1] - 4
    boxes, scores, class_ids = [], [], []
    for det in preds:
        cx, cy, w, h = det[:4]
        cls_scores = det[4:]
        cid = int(np.argmax(cls_scores))
        conf = float(cls_scores[cid])
        if conf < CONF_THRESH:
            continue
        x1 = int((cx - w / 2) * orig_w / INPUT_SIZE)
        y1 = int((cy - h / 2) * orig_h / INPUT_SIZE)
        bw = int(w * orig_w / INPUT_SIZE)
        bh = int(h * orig_h / INPUT_SIZE)
        boxes.append([x1, y1, bw, bh])
        scores.append(conf)
        class_ids.append(cid)
    if not boxes:
        return []
    indices = cv2.dnn.NMSBoxes(boxes, scores, CONF_THRESH, IOU_THRESH)
    results = []
    for idx in (indices.flatten() if isinstance(indices, np.ndarray) else indices):
        x, y, w, h = boxes[idx]
        cid = class_ids[idx]
        label = CLASSES[cid] if cid < len(CLASSES) else f"cls{cid}"
        results.append({"label": label, "class_id": cid, "conf": scores[idx],
                        "box": (x, y, x + w, y + h)})
    return results


def draw(frame: np.ndarray, detections: list) -> np.ndarray:
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        color = COLORS[det["class_id"]] if det["class_id"] < len(COLORS) else (255, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{det['label']} {det['conf']:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, text, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    return frame


def capture_loop():
    global _latest_jpeg, _stats

    print("Loading NCNN model...")
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.load_param(MODEL_PARAM)
    net.load_model(MODEL_BIN)
    print("Model loaded OK.")

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("ERROR: Cannot open /dev/video0")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera: {cam_w}x{cam_h}")

    frame_count = 0
    shape_logged = False
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        img = preprocess(frame)
        with net.create_extractor() as ex:
            ex.input("in0", ncnn.Mat(img).clone())
            _, out0 = ex.extract("out0")

        raw = np.array(out0)
        if not shape_logged:
            shape_str = str(raw.shape)
            print(f"Model output shape: {shape_str}  ({raw.shape[0] - 4} classes)")
            _stats["output_shape"] = shape_str
            shape_logged = True

        detections = postprocess(raw, cam_w, cam_h)
        frame = draw(frame, detections)

        frame_count += 1
        elapsed = time.time() - t0
        if elapsed >= 1.0:
            _stats["fps"] = round(frame_count / elapsed, 1)
            _stats["detections"] = len(detections)
            frame_count = 0
            t0 = time.time()

        # HUD
        cv2.putText(frame, f"FPS: {_stats['fps']}  |  Detected: {len(detections)}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            with _frame_lock:
                _latest_jpeg = buf.tobytes()

    cap.release()
    net.clear()


class MJPEGHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass   # silence access log

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
<!DOCTYPE html><html><head>
<title>Tomato Sorter - Camera Test</title>
<style>
  body { margin: 0; background: #111; display: flex; flex-direction: column;
         align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; color: #eee; }
  h2 { margin-bottom: 12px; color: #f87171; }
  img { border: 2px solid #444; border-radius: 8px; max-width: 100%; }
</style></head><body>
<h2>Tomato Sorter v2.0 &mdash; Live Detection</h2>
<img src="/stream" />
</body></html>""")

        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    with _frame_lock:
                        jpeg = _latest_jpeg
                    if jpeg is None:
                        time.sleep(0.05)
                        continue
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()


def main():
    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()

    # Wait for first frame before starting server
    print("Waiting for first frame...")
    while _latest_jpeg is None:
        time.sleep(0.1)

    server = HTTPServer(("0.0.0.0", 8080), MJPEGHandler)
    print("\n>>> Open Chromium on the Pi and go to: http://localhost:8080 <<<\n")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
