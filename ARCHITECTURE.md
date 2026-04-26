# 🍅 Tomato Sorting System v2.0 — Raspberry Pi 5

**Project:** Production-ready tomato classifier with YOLO + DHT22 environmental monitoring
**Hardware:** Raspberry Pi 5 (8GB) | Debian Trixie | Python 3.13
**Target:** Thesis defense — 5-8 FPS, accurate, kiosk-mode, auto-launching dashboard

---

## 1. Why this rewrite

Old Pi 4 codebase had:
- 30+ Python files, 9 redundant DHT22 scripts, 6 redundant YOLO scripts
- No separation of concerns (sensor + AI + web all mixed)
- Hardcoded config (GPIO pins, IPs, paths)
- Print-statement "logging"
- Models, dataset, and code all jumbled in repo root
- No service management — manual `python3 script.py` per terminal

This v2.0 fixes all of that with a **5-layer architecture** and **3 systemd services**.

---

## 2. Final tech stack

| Concern | Choice | Why |
|---|---|---|
| OS | Debian Trixie (Pi OS) | Already installed, latest LTS |
| Python | 3.13 (system default) | No need for pyenv |
| Inference | NCNN format | 2-3x faster than PyTorch on ARM |
| Web framework | Flask + Flask-SocketIO | Lightweight, real-time updates |
| GPIO library | `gpiozero` + `lgpio` | Pi 5 compatible (RP1 chip) |
| DHT22 library | `adafruit-circuitpython-dht` | Maintained, Pi 5 compatible |
| Camera | `picamera2` | Official, libcamera-based |
| Database | SQLite (built-in) | Zero-config, file-based |
| Process manager | systemd | Auto-start, auto-restart |
| UI launcher | Chromium kiosk mode | Auto-fullscreen on boot |
| Config | YAML (`pyyaml`) | Human-readable, no code |

---

## 3. File structure

```
~/tomato-sorter/
├── README.md
├── pyproject.toml              # Dependencies (modern, no requirements.txt mess)
├── .env.example                # Sample env vars
├── config/
│   └── settings.yaml           # All config in ONE place
├── src/
│   └── tomato_sorter/
│       ├── __init__.py
│       ├── main.py             # Entry point (orchestrator)
│       │
│       ├── hardware/           # Layer 1: Hardware abstraction
│       │   ├── __init__.py
│       │   ├── camera.py       # Picamera2 wrapper
│       │   ├── gpio.py         # gpiozero wrapper
│       │   ├── sensors.py      # DHT22 readers (both sensors)
│       │   └── servo.py        # (future) sorting mechanism
│       │
│       ├── services/           # Layer 2: Core services
│       │   ├── __init__.py
│       │   ├── detector.py     # YOLO NCNN inference
│       │   ├── sensor_reader.py# DHT22 polling loop with caching
│       │   └── classifier.py   # Ripe/unripe + counting logic
│       │
│       ├── app/                # Layer 3: Application logic
│       │   ├── __init__.py
│       │   ├── orchestrator.py # Coordinates services
│       │   ├── state.py        # Single source of truth (state machine)
│       │   └── events.py       # Pub/sub event bus (in-memory)
│       │
│       ├── api/                # Layer 4: Web interface
│       │   ├── __init__.py
│       │   ├── server.py       # Flask app factory
│       │   ├── routes.py       # REST endpoints
│       │   ├── websocket.py    # Real-time updates
│       │   └── templates/
│       │       └── dashboard.html
│       │
│       └── persistence/        # Layer 5: Data storage
│           ├── __init__.py
│           ├── database.py     # SQLite connection + schema
│           ├── models.py       # Detection, SensorReading, Event
│           └── exporter.py     # CSV export utility
│
├── models/                     # Trained weights (NOT in git, downloaded separately)
│   ├── best.ncnn.param
│   └── best.ncnn.bin
│
├── data/                       # SQLite DB + logs (gitignored)
│   ├── sorter.db
│   └── logs/
│       └── sorter.log
│
├── scripts/                    # One-shot utilities
│   ├── install.sh              # Full setup script
│   ├── export_csv.py           # Export DB to CSV for thesis
│   ├── test_camera.py          # Verify camera works
│   ├── test_sensors.py         # Verify DHT22 wiring
│   └── benchmark.py            # FPS + accuracy benchmark
│
├── deploy/                     # systemd + kiosk setup
│   ├── tomato-detector.service
│   ├── tomato-sensors.service
│   ├── tomato-dashboard.service
│   └── kiosk-autostart.sh
│
└── tests/                      # Pytest unit tests (thesis bonus points!)
    ├── test_classifier.py
    ├── test_state.py
    └── test_database.py
```

**Total Python files: ~20** (vs. 30+ in v1) — every file has a single, clear responsibility.

---

## 4. Layer responsibilities

### Layer 1 — Hardware abstraction (`hardware/`)
**Rule:** Knows nothing about YOLO, Flask, or business logic. Pure I/O wrappers.

- `camera.py`: opens Picamera2, returns frames as numpy arrays
- `gpio.py`: Pi 5 GPIO setup using `gpiozero` (handles RP1 chip)
- `sensors.py`: reads both DHT22s with retry logic + caching
- `servo.py`: (future) controls sorting servo motors

### Layer 2 — Core services (`services/`)
**Rule:** Stateless workers. Take input, return output. No web logic.

- `detector.py`: loads NCNN model, runs inference on a frame, returns detections
- `sensor_reader.py`: polling loop, calls `hardware/sensors.py`, publishes to event bus
- `classifier.py`: takes detections, increments counters, applies sorting rules

### Layer 3 — Application logic (`app/`)
**Rule:** The "brain" — coordinates everything. Single source of truth.

- `orchestrator.py`: starts services, manages frame pipeline, publishes events
- `state.py`: holds current state (counts, sensor readings, system status)
- `events.py`: in-memory pub/sub so layers don't directly call each other

### Layer 4 — Web interface (`api/`)
**Rule:** Only talks to Layer 3. Doesn't touch hardware or models directly.

- `server.py`: Flask app factory pattern
- `routes.py`: `/api/state`, `/api/detections`, `/api/sensors`, `/api/export`
- `websocket.py`: pushes real-time state updates to dashboard
- `templates/dashboard.html`: single-page mobile-responsive UI

### Layer 5 — Persistence (`persistence/`)
**Rule:** Only Layer 3 writes to it. Layer 4 reads via API only.

- `database.py`: SQLite connection, migrations, schema
- `models.py`: `Detection`, `SensorReading`, `SystemEvent` dataclasses
- `exporter.py`: dump tables to CSV for thesis analysis

---

## 5. Data model (SQLite schema)

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    class TEXT NOT NULL,           -- 'ripe' or 'unripe'
    confidence REAL NOT NULL,
    bbox_x INTEGER, bbox_y INTEGER,
    bbox_w INTEGER, bbox_h INTEGER
);

CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    container TEXT NOT NULL,       -- 'ripe' or 'unripe'
    temperature REAL,
    humidity REAL,
    is_cached INTEGER DEFAULT 0    -- 1 if reading failed and cached value used
);

CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,           -- 'info', 'warning', 'error'
    component TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX idx_detections_time ON detections(timestamp);
CREATE INDEX idx_sensors_time ON sensor_readings(timestamp);
```

For thesis: simple SQL gives you charts (detections/hour, sensor trends, accuracy over time).

---

## 6. Configuration (`config/settings.yaml`)

ALL config in one file — no hardcoded values anywhere in code:

```yaml
camera:
  resolution: [640, 480]
  framerate: 30

detector:
  model_path: "models/best.ncnn"
  confidence_threshold: 0.5
  iou_threshold: 0.45
  classes: ["unripe", "ripe"]
  inference_size: 480

sensors:
  unripe:
    gpio_pin: 4
    label: "UNRIPE Container"
  ripe:
    gpio_pin: 23
    label: "RIPE Container"
  poll_interval_seconds: 2
  cache_timeout_seconds: 30

database:
  path: "data/sorter.db"

server:
  host: "0.0.0.0"
  port: 5000
  debug: false

logging:
  level: "INFO"
  file: "data/logs/sorter.log"
  max_bytes: 10485760    # 10 MB
  backup_count: 5
```

---

## 7. systemd services

### `deploy/tomato-detector.service`
```ini
[Unit]
Description=Tomato Sorter — YOLO Detector
After=network.target

[Service]
Type=simple
User=bacadasa
WorkingDirectory=/home/bacadasa/tomato-sorter
ExecStart=/home/bacadasa/tomato-sorter/.venv/bin/python -m tomato_sorter.main detector
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### `deploy/tomato-sensors.service`
```ini
[Unit]
Description=Tomato Sorter — DHT22 Sensors
After=network.target

[Service]
Type=simple
User=bacadasa
WorkingDirectory=/home/bacadasa/tomato-sorter
ExecStart=/home/bacadasa/tomato-sorter/.venv/bin/python -m tomato_sorter.main sensors
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### `deploy/tomato-dashboard.service`
```ini
[Unit]
Description=Tomato Sorter — Web Dashboard
After=network.target tomato-detector.service tomato-sensors.service

[Service]
Type=simple
User=bacadasa
WorkingDirectory=/home/bacadasa/tomato-sorter
ExecStart=/home/bacadasa/tomato-sorter/.venv/bin/python -m tomato_sorter.main dashboard
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Install:**
```bash
sudo cp deploy/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tomato-detector tomato-sensors tomato-dashboard
sudo systemctl start tomato-detector tomato-sensors tomato-dashboard
```

**Check status:**
```bash
sudo systemctl status tomato-dashboard
journalctl -u tomato-dashboard -f    # Live logs
```

---

## 8. Chromium kiosk mode auto-launch

**File:** `~/.config/wayfire.ini` (Wayland) or `~/.config/lxsession/LXDE-pi/autostart` (X11)

For Wayland (default Trixie):
```ini
[autostart]
chromium = chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --start-fullscreen http://localhost:5000
```

For X11 (`~/.config/lxsession/LXDE-pi/autostart`):
```
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000
```

**Boot flow:**
1. Pi powers on → systemd starts services (10-15s)
2. Auto-login as `bacadasa` (configured via `raspi-config`)
3. Desktop loads → autostart script runs Chromium in kiosk
4. Dashboard fullscreen at `http://localhost:5000`
5. Total time from power-on to dashboard: **~30 seconds**

---

## 9. Installation order

Step-by-step rebuild plan from a fresh Pi:

### Phase 1 — System prep (15 min)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv python3-dev \
                    python3-picamera2 python3-libcamera \
                    libatlas-base-dev libopenjp2-7 libtiff6 \
                    sqlite3 chromium-browser
```

### Phase 2 — Enable interfaces (5 min)
```bash
sudo raspi-config nonint do_camera 0      # Camera
sudo raspi-config nonint do_i2c 0         # I2C (if needed)
sudo raspi-config nonint do_vnc 0         # VNC (already done)
```

### Phase 3 — Project setup (10 min)
```bash
cd ~
git clone <new-repo-url> tomato-sorter
cd tomato-sorter
python3 -m venv .venv
source .venv/bin/activate
pip install -e .                          # Install from pyproject.toml
```

### Phase 4 — Download model (5 min)
```bash
mkdir -p models
# Convert old best.pt → NCNN format on PC, copy to Pi
# Or: scp best.ncnn.* bacadasa@<pi-ip>:~/tomato-sorter/models/
```

### Phase 5 — Verify hardware (10 min)
```bash
python scripts/test_camera.py           # Should show preview
python scripts/test_sensors.py          # Should print temp + humidity
```

### Phase 6 — Run manually first (5 min)
```bash
python -m tomato_sorter.main all        # Run all services in one process
# Open browser: http://localhost:5000
```

### Phase 7 — Deploy as systemd (10 min)
```bash
sudo cp deploy/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tomato-detector tomato-sensors tomato-dashboard
```

### Phase 8 — Kiosk autostart (5 min)
```bash
# Edit ~/.config/wayfire.ini (Wayland) or autostart (X11)
sudo reboot
# Watch the magic — dashboard opens fullscreen automatically
```

**Total time: ~1 hour** (vs. 5+ hours of debugging in v1)

---

## 10. Migration from old Pi 4 repo

What to **carry over**:
- ✅ `best.pt` → convert to NCNN: `yolo export model=best.pt format=ncnn`
- ✅ Dataset (`public/data/`) → keep on PC for retraining only, NOT on Pi
- ✅ DHT22 wiring diagram — same GPIO pins (4 + 23)
- ✅ Class definitions: `ripe`, `unripe`

What to **leave behind**:
- ❌ All 9 DHT22 scripts → replaced by single `sensor_reader.py`
- ❌ All 6 YOLO scripts → replaced by single `detector.py`
- ❌ `Adafruit_DHT` library (broken on Pi 5) → use `adafruit-circuitpython-dht`
- ❌ `RPi.GPIO` (broken on Pi 5) → use `gpiozero`
- ❌ Hardcoded IPs in code → moved to `config/settings.yaml`
- ❌ `best.pt`, `.7z`, NCNN folder, multiple model variants → just one NCNN model

---

## 11. Performance optimizations for accuracy-first

Since target is **5-8 FPS with high accuracy**:

1. **NCNN inference at 480x480** (matches your old `my_model11n480` size)
2. **Frame queue with single-consumer pattern** — drop frames if detector falls behind, never block camera
3. **Confidence threshold = 0.5** (default) — adjust based on validation
4. **NMS IoU = 0.45** — prevents duplicate boxes
5. **Cache frames** — don't reprocess identical frames
6. **Pi 5 active cooler** strongly recommended — sustained inference heats up CPU; throttling kills FPS

---

## 12. Thesis defense talking points

When the panel asks about the system, you can confidently say:

> *"The system follows a 5-layer architecture with strict separation of concerns. Three systemd services handle detection, sensing, and the web interface independently — each can fail and recover without affecting the others. Configuration is externalized to YAML, all events are logged to SQLite for reproducible analysis, and the system auto-launches in kiosk mode for unattended operation."*

That's a panel-grade architecture description. 🎯

---

## 13. Risks + mitigations

| Risk | Mitigation |
|---|---|
| DHT22 reads fail (40-60% normal) | Caching layer + "REAL vs CACHED" UI badge |
| Pi overheats during long demos | Active cooler + thermal throttling alarm in UI |
| Service crashes mid-defense | systemd auto-restart, logged to journal |
| SD card corruption | Regular DB backups, model on SSD if possible |
| Network drops (Wi-Fi flaky on demo day) | Fully local — `localhost` dashboard, no internet needed |
| YOLO inference too slow | NCNN already optimized; can reduce to 320x320 if needed |

---

## 14. Next steps after architecture approval

1. ✅ Review this doc — flag anything to change
2. ⬜ Create new GitHub repo: `tomato-sorter-pi5`
3. ⬜ Set up `pyproject.toml` with dependencies
4. ⬜ Build skeleton (empty modules with docstrings)
5. ⬜ Convert `best.pt` → NCNN format on your PC
6. ⬜ Implement Layer 1 (hardware) first → test
7. ⬜ Implement Layer 5 (persistence) → test
8. ⬜ Implement Layer 2 (services) → test each in isolation
9. ⬜ Implement Layer 3 (orchestrator) → integration test
10. ⬜ Implement Layer 4 (web UI) last
11. ⬜ Deploy systemd + kiosk
12. ⬜ Run 1-hour stress test before defense

---

**Ready to build, Killua. 🍅🚀**
