"""
The brain — runs the full sort cycle.

State machine:
    IDLE          -> waiting for START
    CONVEYOR      -> tomato traveling toward sort point, camera scans
    SORTING       -> IR triggered, Servo 2+3 flap pair moves to class combo
    SETTLE        -> waiting for tomato to fall into bin
    RETURN        -> Servo 2+3 return to both-open rest
    -> back to CONVEYOR
"""
import logging
import threading
import time

from . import database

log = logging.getLogger("orchestrator")
from .arduino_link import ArduinoLink
from .config import SETTINGS
from .conveyor import ConveyorController
from .detector import Detector
from .state import STATE


class Orchestrator:
    BIN_FOR_CLASS = {"ripe": 1, "unripe": 2, "rotten": 3}

    def __init__(self, arduino: ArduinoLink, detector: Detector,
                 conveyor: ConveyorController = None):
        self.arduino  = arduino
        self.detector = detector
        self.conveyor = conveyor
        self._cycle_cfg = SETTINGS["cycle"]
        self._fallback  = self._cycle_cfg["fallback_class"]
        self._thread = None
        self._stop_evt = threading.Event()
        self._latest_class: str = self._fallback
        self._latest_conf: float = 0.0
        self._latest_box = (0, 0, 0, 0)
        # Track IR by timestamp + current state — avoids edge-event race
        self._ir_state = "CLEAR"
        self._last_ir_trigger_ts: float = 0.0
        self._consumed_ir_trigger_ts: float = 0.0
        self._last_sort_ts: float = 0.0

    # called from arduino reader thread when IR fires
    def on_ir(self, line: str):
        if line == "IR:TRIGGERED":
            self._ir_state = "TRIGGERED"
            self._last_ir_trigger_ts = time.time()
            STATE.update(ir_state="TRIGGERED")
            # Diagnostic: push every IR fire to the dashboard event feed.
            # Lets us SEE whether IR is reaching the orchestrator, even
            # outside an active cycle.
            cycle_state = "during cycle" if STATE.snapshot()["cycle_running"] else "idle"
            STATE.push_event(f"IR:TRIGGERED ({cycle_state})")
        elif line == "IR:CLEAR":
            self._ir_state = "CLEAR"
            STATE.update(ir_state="CLEAR")

    def simulate_ir_trigger(self):
        """Debug: simulate an IR fire and IMMEDIATELY sort using the
        latest camera detection, bypassing the cycle loop.

        If this works → camera + servo logic is sound; problem is
        only in the physical IR sensor path.
        """
        self.on_ir("IR:TRIGGERED")
        STATE.push_event("IR:TRIGGERED (SIMULATED)")

        # Directly trigger a sort using whatever the camera sees right now.
        d = self.detector.best_detection()
        if d is None:
            STATE.push_event("Simulated IR fired, but camera sees no tomato — defaulting to unripe")
            best_class = self._fallback
            best_conf  = 0.0
            best_box   = (0, 0, 0, 0)
        else:
            best_class = d.label
            best_conf  = d.conf
            best_box   = d.box

        STATE.update(tomato_index=STATE.snapshot()["tomato_index"] + 1)
        idx    = STATE.snapshot()["tomato_index"]
        bin_no = self.BIN_FOR_CLASS.get(best_class, 2)

        STATE.push_event(f"SIMULATED Sort #{idx} as {best_class.upper()} (Bin {bin_no})")
        STATE.push_timeline({
            "index": idx,
            "ts":     time.strftime("%H:%M:%S"),
            "class":  best_class,
            "conf":   round(best_conf, 2),
            "bin":    bin_no,
        })
        database.log_detection(best_class, best_conf, best_box, sorted_to=bin_no)

        # Move flap pair
        if best_class == "ripe":
            self.arduino.sort_ripe()
            STATE.update(sorter_position="LEFT")
        elif best_class == "rotten":
            self.arduino.sort_rotten()
            STATE.update(sorter_position="RIGHT")
        else:
            self.arduino.sort_unripe()
            STATE.update(sorter_position="CENTER")

        # Hold + return to rest
        time.sleep(self._cycle_cfg["sort_settle_ms"] / 1000.0)
        if best_class != "rotten":
            self.arduino.sort_rotten()
            STATE.update(sorter_position="RIGHT")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        # Ignore stale IR fires that happened while idle, then consume any
        # new trigger that happens while the run is active.
        self._consumed_ir_trigger_ts = self._last_ir_trigger_ts
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
            # Home all hardware to default rest pose before the first cycle.
            # Servo 4 -> CLOSED (auto-osc paused while we settle).
            # Servo 2+3 -> both OPEN.
            STATE.push_event("Homing servos to default position")
            self.arduino.home_all()
            time.sleep(0.8)                 # let servos physically settle

            # Now arm the Servo 4 oscillator for the run.
            self.arduino.servo4_auto_on()
            STATE.push_event("Servo 4 auto-oscillator armed")

            # Start the conveyor moving forward — tomatoes can now feed.
            if self.conveyor:
                self.conveyor.forward()
                STATE.update(conveyor_state="FORWARD")
                STATE.push_event("Conveyor FORWARD")

            while not self._stop_evt.is_set():
                self._one_cycle()
                time.sleep(self._cycle_cfg["rest_between_ms"] / 1000.0)
        finally:
            # Stop the oscillator and park Servo 4 closed when the cycle ends.
            try:
                self.arduino.servo4_auto_off()
                self.arduino.servo4_close()
            except Exception:
                pass
            # Stop the conveyor when the cycle ends.
            if self.conveyor:
                try:
                    self.conveyor.stop()
                    STATE.update(conveyor_state="STOPPED")
                    STATE.push_event("Conveyor STOPPED")
                except Exception:
                    pass
            STATE.update(cycle_running=False)

    def _one_cycle(self):
        cycle_start_ts = time.time()
        log.info("=== _one_cycle START ===")

        # 1) Camera continuously classifies; we WAIT FOR IR TRIGGER.
        #    Servo 2+3 will NOT fire unless the IR sensor actually catches the tomato.
        STATE.push_event("Watching conveyor — waiting for IR sensor")
        timeout        = self._cycle_cfg["conveyor_travel_ms"] / 1000.0
        min_travel     = self._cycle_cfg.get("min_travel_ms", 0) / 1000.0
        cooldown       = self._cycle_cfg.get("ir_sort_cooldown_ms", 0) / 1000.0
        ir_valid_after = cycle_start_ts + min_travel
        best_conf = 0.0
        best_class = None
        best_box = (0, 0, 0, 0)

        ir_caught = False

        while time.time() - cycle_start_ts < timeout and not self._stop_evt.is_set():
            # Camera continuously classifies (keep highest-confidence detection)
            d = self.detector.best_detection()
            if d and d.conf > best_conf:
                best_conf = d.conf
                best_class = d.label
                best_box = d.box

            # Consume one valid IR fire per cycle. Early/noisy triggers and
            # repeat triggers right after a sort are ignored.
            if (self._last_ir_trigger_ts > self._consumed_ir_trigger_ts and
                self._last_ir_trigger_ts >= ir_valid_after and
                time.time() - self._last_sort_ts >= cooldown):
                ir_caught = True
                self._consumed_ir_trigger_ts = self._last_ir_trigger_ts
                log.info(f"IR caught! ts={self._last_ir_trigger_ts:.3f} "
                         f"best_class={best_class} conf={best_conf:.2f}")
                break
            time.sleep(0.05)

        log.info(f"=== loop ended: ir_caught={ir_caught} elapsed={time.time()-cycle_start_ts:.1f}s "
                 f"best_class={best_class} best_conf={best_conf:.2f} ===")

        if self._stop_evt.is_set():
            return

        # 3) Decide based on IR — Servo 2 ONLY moves if IR caught the tomato
        if not ir_caught:
            STATE.push_event(f"IR did NOT trigger in {timeout:.0f}s — skipping sort (flaps stay open)")
            database.log_event("warning", "orchestrator",
                               f"IR timeout, no sort. Camera saw best={best_class} conf={best_conf:.2f}")
            return

        # IR triggered → sort using latest camera classification
        ir_delay_ms = (time.time() - cycle_start_ts) * 1000

        if best_class is None and self._cycle_cfg.get("require_detection", True):
            STATE.push_event("IR triggered, but camera sees no tomato — skipping sort")
            database.log_event("warning", "orchestrator", "IR trigger ignored because camera had no detection")
            return

        # Optional fallback for demos where a missed camera frame should still sort.
        if best_class is None:
            best_class = self._fallback
            STATE.push_event(f"IR caught tomato but camera missed — defaulting to {best_class}")

        STATE.update(tomato_index=STATE.snapshot()["tomato_index"] + 1)
        idx = STATE.snapshot()["tomato_index"]

        bin_no = self.BIN_FOR_CLASS.get(best_class, 2)
        STATE.push_event(f"IR triggered after {ir_delay_ms:.0f}ms → Sort #{idx} as {best_class.upper()} (Bin {bin_no})")
        STATE.push_timeline({
            "index": idx,
            "ts":     time.strftime("%H:%M:%S"),
            "class":  best_class,
            "conf":   round(best_conf, 2),
            "bin":    bin_no,
        })
        database.log_detection(best_class, best_conf, best_box, sorted_to=bin_no)

        # 4) Move Servo 2+3 flap pair NOW (only after IR triggered)
        sort_delay_ms = self._cycle_cfg.get("ir_sort_delay_ms", 0)
        if sort_delay_ms > 0:
            STATE.push_event(f"IR caught tomato — sorting in {sort_delay_ms}ms")
            time.sleep(sort_delay_ms / 1000.0)

        if best_class == "ripe":
            self.arduino.sort_ripe()
            STATE.update(sorter_position="LEFT")
        elif best_class == "rotten":
            self.arduino.sort_rotten()
            STATE.update(sorter_position="RIGHT")
        else:
            self.arduino.sort_unripe()
            STATE.update(sorter_position="CENTER")
        self._last_sort_ts = time.time()

        # 5) Hold position so tomato falls into bin
        time.sleep(self._cycle_cfg["sort_settle_ms"] / 1000.0)

        # 6) Return to both-open rest position
        if best_class != "rotten":
            self.arduino.sort_rotten()
            STATE.update(sorter_position="RIGHT")
            time.sleep(0.4)
