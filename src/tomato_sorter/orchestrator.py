"""
The brain — runs the full sort cycle.

State machine:
    IDLE          -> waiting for START
    GATE_OPEN     -> Servo 1 open, drop 1 tomato
    CONVEYOR      -> tomato traveling toward sort point, camera scans
    SORTING       -> IR triggered, Servo 2 rotates to bin
    SETTLE        -> waiting for tomato to fall into bin
    RETURN        -> Servo 2 back to center
    -> back to GATE_OPEN
"""
import threading
import time

from . import database
from .arduino_link import ArduinoLink
from .config import SETTINGS
from .detector import Detector
from .state import STATE


class Orchestrator:
    BIN_FOR_CLASS = {"ripe": 1, "unripe": 2, "rotten": 3}

    def __init__(self, arduino: ArduinoLink, detector: Detector):
        self.arduino  = arduino
        self.detector = detector
        self._cycle_cfg = SETTINGS["cycle"]
        self._fallback  = self._cycle_cfg["fallback_class"]
        self._thread = None
        self._stop_evt = threading.Event()
        self._ir_evt = threading.Event()
        self._latest_class: str = self._fallback
        self._latest_conf: float = 0.0
        self._latest_box = (0, 0, 0, 0)

    # called from arduino reader thread when IR fires
    def on_ir(self, line: str):
        if line == "IR:TRIGGERED":
            STATE.update(ir_state="TRIGGERED")
            self._ir_evt.set()
        elif line == "IR:CLEAR":
            STATE.update(ir_state="CLEAR")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        STATE.update(cycle_running=True)
        STATE.push_event("Cycle STARTED")
        database.log_event("info", "orchestrator", "cycle started")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()
        STATE.update(cycle_running=False)
        STATE.push_event("Cycle STOPPED")
        database.log_event("info", "orchestrator", "cycle stopped")

    # ---- main loop ----
    def _loop(self):
        try:
            self.arduino.gate_close()
            self.arduino.sort_unripe()      # center = rest
            time.sleep(0.6)

            while not self._stop_evt.is_set():
                self._one_cycle()
                time.sleep(self._cycle_cfg["rest_between_ms"] / 1000.0)
        finally:
            STATE.update(cycle_running=False)

    def _one_cycle(self):
        # 1) Drop one tomato
        STATE.push_event("Opening gate to release tomato")
        STATE.update(gate_position="OPEN")
        self.arduino.gate_open()
        time.sleep(self._cycle_cfg["gate_open_hold_ms"] / 1000.0)
        self.arduino.gate_close()
        STATE.update(gate_position="CLOSED")

        # 2) Wait for IR to trigger (tomato reached sort point)
        STATE.push_event("Tomato on conveyor — scanning")
        self._ir_evt.clear()
        timeout = self._cycle_cfg["conveyor_travel_ms"] / 1000.0
        start = time.time()
        best_conf = 0.0
        best_class = self._fallback
        best_box = (0, 0, 0, 0)
        while time.time() - start < timeout and not self._stop_evt.is_set():
            d = self.detector.best_detection()
            if d and d.conf > best_conf:
                best_conf = d.conf
                best_class = d.label
                best_box = d.box
            if self._ir_evt.wait(timeout=0.05):
                break

        if self._stop_evt.is_set():
            return

        STATE.update(tomato_index=STATE.snapshot()["tomato_index"] + 1)
        idx = STATE.snapshot()["tomato_index"]

        # 3) Sort
        bin_no = self.BIN_FOR_CLASS.get(best_class, 2)
        STATE.push_event(f"Tomato #{idx} -> {best_class.upper()} (Bin {bin_no})")
        STATE.push_timeline({
            "index": idx,
            "ts":     time.strftime("%H:%M:%S"),
            "class":  best_class,
            "conf":   round(best_conf, 2),
            "bin":    bin_no,
        })
        database.log_detection(best_class, best_conf, best_box, sorted_to=bin_no)

        if best_class == "ripe":
            self.arduino.sort_ripe()
            STATE.update(sorter_position="LEFT")
        elif best_class == "rotten":
            self.arduino.sort_rotten()
            STATE.update(sorter_position="RIGHT")
        else:
            self.arduino.sort_unripe()
            STATE.update(sorter_position="CENTER")

        time.sleep(self._cycle_cfg["sort_settle_ms"] / 1000.0)

        # 4) Return to center
        if best_class != "unripe":
            self.arduino.sort_unripe()
            STATE.update(sorter_position="CENTER")
            time.sleep(0.4)
