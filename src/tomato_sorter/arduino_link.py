"""
Pi <-> Arduino serial link.

Wraps the protocol defined by the Arduino firmware in arduino/sketches/tomato_sorter.

Public methods are blocking but quick (just write a line).
Inbound async events (IR:TRIGGERED, IR:CLEAR) are dispatched to a callback.
"""
import threading
import time
from collections import deque
from typing import Callable, Optional

import serial

from .config import SETTINGS


class ArduinoLink:
    def __init__(self, on_event: Optional[Callable[[str], None]] = None):
        self._cfg = SETTINGS["arduino"]
        self._ser: Optional[serial.Serial] = None
        self._running = False
        self._on_event = on_event
        self._reader_thread: Optional[threading.Thread] = None
        self._write_lock = threading.Lock()
        self._inbox = deque(maxlen=100)

    # ------------- lifecycle -------------
    def start(self):
        self._ser = serial.Serial(self._cfg["port"], self._cfg["baud"],
                                  timeout=self._cfg["timeout"])
        time.sleep(2)   # let Arduino reboot finish (DTR auto-reset)
        self._ser.reset_input_buffer()
        self._running = True
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def stop(self):
        self._running = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass

    def _reader_loop(self):
        while self._running and self._ser:
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
            except Exception:
                continue
            if not line:
                continue
            self._inbox.append((time.time(), line))
            if self._on_event:
                try:
                    self._on_event(line)
                except Exception:
                    pass

    # ------------- writes -------------
    def _send(self, cmd: str):
        if not self._ser:
            return
        with self._write_lock:
            self._ser.write((cmd + "\n").encode())
            self._ser.flush()

    # gate
    def gate_open(self):  self._send("SERVO1:OPEN")
    def gate_close(self): self._send("SERVO1:CLOSE")

    # servo 4
    def servo4_open(self):  self._send("SERVO4:OPEN")
    def servo4_close(self): self._send("SERVO4:CLOSE")

    # sorter flap pair:
    # ripe   -> Servo 2 closed + Servo 3 open
    # unripe -> Servo 2 open + Servo 3 closed
    # rotten -> Servo 2 open + Servo 3 open
    def sort_ripe(self):    self._send("SERVO2:LEFT")
    def sort_unripe(self):  self._send("SERVO2:CENTER")
    def sort_rotten(self):  self._send("SERVO2:RIGHT")
    def sort_for(self, cls: str):
        if cls == "ripe":
            self.sort_ripe()
        elif cls == "rotten":
            self.sort_rotten()
        else:
            self.sort_unripe()

    # relays
    def relay1(self, on: bool): self._send(f"RELAY1:{'ON' if on else 'OFF'}")
    def relay2(self, on: bool): self._send(f"RELAY2:{'ON' if on else 'OFF'}")

    # diagnostics
    def ping(self):   self._send("PING")
    def status(self): self._send("STATUS")

    def recent_inbox(self, n: int = 20):
        return list(self._inbox)[-n:]
