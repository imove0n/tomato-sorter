"""SQLite persistence layer."""
import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Optional

from .config import PROJECT_ROOT, SETTINGS

_DB_PATH = PROJECT_ROOT / SETTINGS["database"]["path"]
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    class TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox_x INTEGER, bbox_y INTEGER,
    bbox_w INTEGER, bbox_h INTEGER,
    sorted_to INTEGER
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    container TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    is_cached INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    component TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_detections_time ON detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensors_time   ON sensor_readings(timestamp);
"""


def _connect():
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock, _connect() as conn:
        conn.executescript(SCHEMA)


def log_detection(cls: str, conf: float, bbox: tuple, sorted_to: int):
    x, y, w, h = bbox
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO detections (class, confidence, bbox_x, bbox_y, bbox_w, bbox_h, sorted_to) "
            "VALUES (?,?,?,?,?,?,?)",
            (cls, conf, x, y, w, h, sorted_to),
        )


def log_sensor(container: str, temp: Optional[float], hum: Optional[float], cached: bool):
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO sensor_readings (container, temperature, humidity, is_cached) VALUES (?,?,?,?)",
            (container, temp, hum, 1 if cached else 0),
        )


def log_event(level: str, component: str, message: str):
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO system_events (level, component, message) VALUES (?,?,?)",
            (level, component, message),
        )


def recent_detections(limit: int = 10) -> List[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, class, confidence, sorted_to "
            "FROM detections ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def reset_all():
    """Wipe detections, sensor readings, and events. Resets all bin counters to 0."""
    with _lock, _connect() as conn:
        conn.executescript("""
            DELETE FROM detections;
            DELETE FROM sensor_readings;
            DELETE FROM system_events;
            DELETE FROM sqlite_sequence;
        """)


def total_counts() -> dict:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT class, COUNT(*) AS n FROM detections WHERE sorted_to IS NOT NULL GROUP BY class"
        ).fetchall()
    out = {"ripe": 0, "unripe": 0, "rotten": 0}
    for r in rows:
        if r["class"] in out:
            out[r["class"]] = r["n"]
    return out
