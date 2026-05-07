"""Flask + SocketIO web server for the SCADA dashboard."""
import subprocess
import threading
import time

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO

from . import database
from .arduino_link import ArduinoLink
from .config import SETTINGS
from .conveyor import ConveyorController
from .detector import Detector
from .orchestrator import Orchestrator
from .sensors import SensorService
from .state import STATE


def create_app(detector: Detector, sensors: SensorService,
               arduino: ArduinoLink, orchestrator: Orchestrator,
               conveyor: ConveyorController):
    app = Flask(__name__,
                template_folder="templates",
                static_folder="static")
    sock = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

    # ----------------- ROUTES -----------------
    @app.route("/")
    def index():
        return render_template("dashboard.html")

    @app.route("/stream")
    def stream():
        def gen():
            while True:
                jpeg = detector.latest_jpeg()
                if jpeg:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                           + jpeg + b"\r\n")
                time.sleep(0.05)
        return Response(gen(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/api/state")
    def api_state():
        snap = STATE.snapshot()
        snap["fps"]      = round(detector.fps(), 1)
        snap["sensors"]  = sensors.snapshot()
        snap["recent"]   = database.recent_detections(10)
        snap["live_detections"] = detector.latest_detections()
        return jsonify(snap)

    @app.route("/api/detections")
    def api_detections():
        """Diagnostic: shows what the detector currently sees."""
        return jsonify({
            "fps": round(detector.fps(), 1),
            "detections": detector.latest_detections(),
        })

    @app.route("/api/analytics")
    def api_analytics():
        """Full persisted sorting history for the expanded analytics view."""
        rows = database.all_detections()
        counts = {"ripe": 0, "unripe": 0, "rotten": 0}
        sorted_rows = 0
        confidence_sum = 0.0
        for row in rows:
            cls = row.get("class")
            if row.get("sorted_to") is not None:
                sorted_rows += 1
                if cls in counts:
                    counts[cls] += 1
            confidence_sum += float(row.get("confidence") or 0.0)
        return jsonify({
            "counts": counts,
            "total": sorted_rows,
            "detections_seen": len(rows),
            "avg_confidence": (confidence_sum / len(rows)) if rows else None,
            "first_timestamp": rows[0]["timestamp"] if rows else None,
            "last_timestamp": rows[-1]["timestamp"] if rows else None,
            "detections": rows,
        })

    @app.route("/api/arduino/inbox")
    def api_arduino_inbox():
        """Diagnostic: shows last 20 messages received from Arduino."""
        msgs = arduino.recent_inbox(20)
        return jsonify({
            "messages": [
                {"ts": ts, "line": line} for ts, line in msgs
            ]
        })

    @app.route("/api/start", methods=["POST"])
    def api_start():
        orchestrator.start()
        return jsonify(ok=True)

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        orchestrator.stop()
        return jsonify(ok=True)

    @app.route("/api/system/shutdown", methods=["POST"])
    def api_system_shutdown():
        """Power off the Pi cleanly. Service tearings happen via systemd."""
        STATE.push_event("System SHUTDOWN requested from dashboard")
        # Schedule the shutdown a beat later so this HTTP response can return.
        threading.Thread(
            target=lambda: (time.sleep(1), subprocess.Popen(["sudo", "/sbin/poweroff"])),
            daemon=True,
        ).start()
        return jsonify(ok=True, action="shutdown")

    @app.route("/api/system/reboot", methods=["POST"])
    def api_system_reboot():
        STATE.push_event("System REBOOT requested from dashboard")
        threading.Thread(
            target=lambda: (time.sleep(1), subprocess.Popen(["sudo", "/sbin/reboot"])),
            daemon=True,
        ).start()
        return jsonify(ok=True, action="reboot")

    @app.route("/api/system/exit_kiosk", methods=["POST"])
    def api_system_exit_kiosk():
        """Close Chromium so the user lands back on the Pi desktop.
        Backend keeps running — they can still come back via browser."""
        STATE.push_event("Exiting kiosk — Chromium closing")
        threading.Thread(
            target=lambda: (time.sleep(0.5), subprocess.Popen(["pkill", "-f", "chromium"])),
            daemon=True,
        ).start()
        return jsonify(ok=True, action="exit_kiosk")

    @app.route("/api/debug/ir_trigger", methods=["POST"])
    def api_debug_ir_trigger():
        """Debug-only: simulate an IR:TRIGGERED message from the Arduino.
        Lets us test the camera→IR→servo pipeline without working IR hardware."""
        orchestrator.simulate_ir_trigger()
        return jsonify(ok=True, simulated=True)

    @app.route("/api/reset", methods=["POST"])
    def api_reset():
        """Wipe all bin counts, timeline, and history. Use before a fresh demo."""
        orchestrator.stop()
        database.reset_all()
        STATE.update(tomato_index=0)
        STATE.timeline.clear()
        STATE.push_event("All counts and history reset")
        return jsonify(ok=True)

    @app.route("/api/manual/<action>", methods=["POST"])
    def api_manual(action):
        if action == "conveyor_forward": conveyor.forward(); STATE.update(conveyor_state="FORWARD")
        elif action == "conveyor_reverse": conveyor.reverse(); STATE.update(conveyor_state="REVERSE")
        elif action == "conveyor_stop": conveyor.stop(); STATE.update(conveyor_state="STOPPED")
        elif action == "servo4_open":  arduino.servo4_open()
        elif action == "servo4_close": arduino.servo4_close()
        elif action == "sort_ripe":   arduino.sort_ripe();   STATE.update(sorter_position="LEFT")
        elif action == "sort_unripe": arduino.sort_unripe(); STATE.update(sorter_position="CENTER")
        elif action == "sort_rotten": arduino.sort_rotten(); STATE.update(sorter_position="RIGHT")
        elif action == "fan1_on":  arduino.relay1(True);  STATE.update(fan1_on=True)
        elif action == "fan1_off": arduino.relay1(False); STATE.update(fan1_on=False)
        elif action == "fan2_on":  arduino.relay2(True);  STATE.update(fan2_on=True)
        elif action == "fan2_off": arduino.relay2(False); STATE.update(fan2_on=False)
        elif action == "arduino_status": arduino.status()
        else:
            return jsonify(ok=False, error="unknown action"), 400
        STATE.push_event(f"Manual: {action}")
        return jsonify(ok=True)

    # ----------------- BROADCAST LOOP -----------------
    def broadcast_loop():
        while True:
            snap = STATE.snapshot()
            snap["fps"]     = round(detector.fps(), 1)
            snap["sensors"] = sensors.snapshot()
            snap["recent"]  = database.recent_detections(10)
            sock.emit("state", snap)
            time.sleep(0.5)

    threading.Thread(target=broadcast_loop, daemon=True).start()

    return app, sock
