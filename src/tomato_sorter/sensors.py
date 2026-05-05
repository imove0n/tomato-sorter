"""DHT22 polling thread with caching for failed reads."""
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

import adafruit_dht
import board

from .config import SETTINGS
from . import database

_PIN_MAP = {
    4:  board.D4,
    23: board.D23,
}


@dataclass
class Reading:
    temp:    Optional[float]
    hum:     Optional[float]
    cached:  bool
    age_sec: float


class _SensorChannel:
    def __init__(self, key: str, gpio_pin: int, label: str):
        self.key = key
        self.label = label
        self._dht = adafruit_dht.DHT22(_PIN_MAP[gpio_pin], use_pulseio=False)
        self._last_temp: Optional[float] = None
        self._last_hum:  Optional[float] = None
        self._last_real_ts: float = 0.0

    def read(self) -> Reading:
        try:
            t = self._dht.temperature
            h = self._dht.humidity
            if t is not None and h is not None:
                self._last_temp = t
                self._last_hum  = h
                self._last_real_ts = time.time()
                database.log_sensor(self.key, t, h, cached=False)
                return Reading(t, h, False, 0.0)
        except RuntimeError:
            pass
        # fall back to cache
        age = time.time() - self._last_real_ts if self._last_real_ts else float("inf")
        database.log_sensor(self.key, self._last_temp, self._last_hum, cached=True)
        return Reading(self._last_temp, self._last_hum, True, age)


class SensorService:
    """Background thread reading both DHT22s on a configurable interval."""

    def __init__(self):
        cfg = SETTINGS["sensors"]
        self._interval = cfg["poll_interval_seconds"]
        sim = cfg.get("simulate", {})
        self._sim_target = "unripe" if sim.get("unripe_from") else None
        self._sim_source = sim.get("unripe_from")
        self._sim_delay = float(sim.get("delay_seconds", 0))
        self._channels = [
            _SensorChannel(key, cfg[key]["gpio_pin"], cfg[key]["label"])
            for key in ("ripe", "unripe")
            if key != self._sim_target
        ]
        self._readings: dict[str, Reading] = {}
        self._history: dict[str, deque[tuple[float, Reading]]] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            for ch in self._channels:
                r = ch.read()
                now = time.time()
                with self._lock:
                    self._readings[ch.key] = r
                    hist = self._history.setdefault(ch.key, deque(maxlen=120))
                    hist.append((now, r))
                time.sleep(0.5)   # DHT22 needs spacing between reads
            self._apply_simulated_reading()
            time.sleep(max(0, self._interval - len(self._channels) * 0.5))

    def _apply_simulated_reading(self):
        if not self._sim_target or not self._sim_source:
            return

        now = time.time()
        cutoff = now - self._sim_delay
        with self._lock:
            hist = self._history.get(self._sim_source)
            if not hist:
                return

            chosen_ts, chosen = hist[0]
            for ts, reading in hist:
                if ts <= cutoff:
                    chosen_ts, chosen = ts, reading
                else:
                    break

            simulated = Reading(chosen.temp, chosen.hum, True, now - chosen_ts)
            self._readings[self._sim_target] = simulated

        database.log_sensor(self._sim_target, simulated.temp, simulated.hum, cached=True)

    def snapshot(self) -> dict:
        with self._lock:
            out = {}
            for k, r in self._readings.items():
                # Convert infinity to null for valid JSON
                age = None if r.age_sec == float("inf") else round(r.age_sec, 1)
                out[k] = {
                    "temp":    r.temp,
                    "hum":     r.hum,
                    "cached":  r.cached,
                    "age_sec": age,
                }
            return out
