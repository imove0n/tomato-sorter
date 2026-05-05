"""Shared system state — single source of truth for the dashboard."""
import threading
import time
from collections import deque

from . import database


class SystemState:
    def __init__(self):
        self._lock = threading.Lock()
        # status flags
        self.cycle_running = False        # auto sort cycle ON/OFF
        self.fan1_on = True
        self.fan2_on = True
        self.conveyor_state = "STOPPED"
        self.gate_position = "CLOSED"     # CLOSED / OPEN
        self.sorter_position = "CENTER"   # LEFT / CENTER / RIGHT
        self.ir_state = "CLEAR"
        self.last_event = ""
        self.last_event_ts = 0.0
        self.tomato_index = 0
        # rolling timeline (recent classifications)
        self.timeline = deque(maxlen=20)

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def push_event(self, msg: str):
        with self._lock:
            self.last_event = msg
            self.last_event_ts = time.time()

    def push_timeline(self, entry: dict):
        with self._lock:
            self.timeline.appendleft(entry)

    def snapshot(self) -> dict:
        counts = database.total_counts()
        with self._lock:
            return {
                "cycle_running":  self.cycle_running,
                "fan1_on":        self.fan1_on,
                "fan2_on":        self.fan2_on,
                "conveyor":       self.conveyor_state,
                "gate":           self.gate_position,
                "sorter":         self.sorter_position,
                "ir":             self.ir_state,
                "last_event":     self.last_event,
                "tomato_index":   self.tomato_index,
                "counts":         counts,
                "timeline":       list(self.timeline),
            }


STATE = SystemState()
