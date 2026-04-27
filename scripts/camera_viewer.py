#!/usr/bin/env python3
"""
Live camera viewer — opens a separate window showing the dashboard's
MJPEG stream with YOLO detection boxes overlaid.

This connects to the RUNNING dashboard at http://localhost:5000/stream
so the dashboard must be running first.

Run:
    .venv/bin/python scripts/camera_viewer.py

Press Q to close the window.
"""
import os
import sys
import urllib.request
import cv2
import numpy as np

# Force Qt to use X11 (works through VNC; Wayland breaks Qt over VNC)
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("DISPLAY", ":0")

URL = "http://localhost:5000/stream"


def main():
    print(f"Connecting to {URL} ...")
    try:
        stream = urllib.request.urlopen(URL, timeout=5)
    except Exception as e:
        print(f"ERROR: cannot connect ({e}). Is the dashboard running on port 5000?")
        sys.exit(1)
    print("Connected. Press Q in the window to quit.")

    buf = b""
    while True:
        buf += stream.read(4096)
        a = buf.find(b"\xff\xd8")        # JPEG start of image
        b = buf.find(b"\xff\xd9", a)     # JPEG end of image
        if a != -1 and b != -1:
            jpeg = buf[a : b + 2]
            buf  = buf[b + 2 :]
            arr  = np.frombuffer(jpeg, dtype=np.uint8)
            img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow("Tomato Sorter — Live Camera", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
