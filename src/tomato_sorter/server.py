"""Flask + SocketIO web server for the SCADA dashboard."""
import threading
import time

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO

from . import database
from .arduino_link import ArduinoLink
from .config import SETTINGS
from .detector import Detector
from .orchestrator import Orchestrator
from .sensors import SensorService
from .state import STATE


def create_app(detector: Detector, sensors: SensorService,
               arduino: ArduinoLink, orchestrator: Orchestrator):
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

    @app.route("/api/manual/<action>", methods=["POST"])
    def api_manual(action):
        if action == "gate_open":   arduino.gate_open();   STATE.update(gate_position="OPEN")
        elif action == "gate_close": arduino.gate_close(); STATE.update(gate_position="CLOSED")
        elif action == "sort_ripe":   arduino.sort_ripe();   STATE.update(sorter_position="LEFT")
        elif action == "sort_unripe": arduino.sort_unripe(); STATE.update(sorter_position="CENTER")
        elif action == "sort_rotten": arduino.sort_rotten(); STATE.update(sorter_position="RIGHT")
        elif action == "fan1_on":  arduino.relay1(True);  STATE.update(fan1_on=True)
        elif action == "fan1_off": arduino.relay1(False); STATE.update(fan1_on=False)
        elif action == "fan2_on":  arduino.relay2(True);  STATE.update(fan2_on=True)
        elif action == "fan2_off": arduino.relay2(False); STATE.update(fan2_on=False)
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
