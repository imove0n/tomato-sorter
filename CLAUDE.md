# CLAUDE.md — Tomato Sorter v2.0 Project Context

> **This file is auto-loaded by Claude Code on every session.** It contains everything you need to know about this project, the user, and where we are in the build.

---

## 👤 About the user

**Name:** Laurence De Guzman (goes by **"Killua"** informally)
**Email:** laurence.deguzman@tup.edu.ph
**School:** Technological University of the Philippines (TUP Manila graduate)
**Day job:** IT Technical Support at Accupoint System Inc. (Quezon City) — sole IT person, but actually does Odoo ERP, AI chatbots, n8n automation, full-stack dev
**Location:** Quezon City, Philippines

### Communication preferences

- **Language:** Casual **Taglish** (Tagalog-English mix). Use it naturally — don't force pure English.
- **Tone:** Direct, casual, friend-to-friend. Address him as "bro" or "Killua" naturally.
- **Pushback:** He prefers **direct, honest pushback**. If something is a bad idea, say so. Don't sugarcoat. He second-guesses decisions mid-process (especially pricing/scope) and benefits from being grounded.
- **Length:** Prefers **short, conversational replies** over long blocks of text. Get to the point fast.
- **Format:** Avoid heavy formatting unless explaining architecture or step-by-step instructions. For casual back-and-forth, plain conversational text is better.

### Technical background

Strong self-teacher. Stack he's comfortable with:
- Python, JavaScript/TypeScript, Next.js, React
- Odoo customization, PostgreSQL, Docker
- REST APIs, cloud infrastructure (Cloudflare, Vercel, AWS Amplify)
- n8n automation, AI chatbot integration
- Has built a SaaS product (NuVista — HOA management system)

He doesn't need basic explanations of programming concepts — just the specifics of this project's tech.

---

## 🍅 Project: Tomato Sorter v2.0

### Context

This is a **rebuild** of an earlier Pi 4 project (`RASPI-4-SORTING-PROJECT4` on his GitHub). The Pi 4 version was:

- **Underperforming** — 4-5 FPS, slow, laggy
- **Architecturally messy** — 30+ Python files, 9 redundant DHT22 scripts, 6 redundant YOLO scripts, no separation of concerns, hardcoded config everywhere
- **Functional but not defensible** — works but hard to explain to thesis panel

**Purpose of v2.0:** Clean rebuild on **Raspberry Pi 5 (8GB)** for **thesis defense**, with production-ready architecture.

### Original repo (for reference, DO NOT clone the whole thing — it's 746MB)

`https://github.com/imove0n/RASPI-4-SORTING-PROJECT4`

What's worth carrying over:
- ✅ `best.pt` (trained YOLO weights — needs conversion to NCNN)
- ✅ DHT22 wiring (GPIO 4 = unripe, GPIO 23 = ripe) — same on Pi 5
- ✅ Class definitions: `ripe`, `unripe`
- ❌ Everything else — rewrite from scratch

### Project goal

> AI-powered tomato sorting system using YOLO object detection on Raspberry Pi 5, with dual DHT22 environmental monitoring (one per container) and a real-time web dashboard. Thesis defense demo: power on Pi → 30 seconds later → kiosk dashboard live, fully autonomous.

---

## 🎯 Locked-in decisions (don't second-guess these)

| Decision | Choice | Why |
|---|---|---|
| **Scope** | Production-ready for thesis defense | Not just "works" — must be defensible |
| **Inference location** | Pi 5 standalone (no PC offload) | No "if PC dies, demo dies" risk |
| **Performance priority** | Accuracy over speed (5-8 FPS OK) | Thesis grades accuracy, not FPS |
| **Model format** | **NCNN** (not PyTorch .pt) | 2-3x faster on ARM, optimized for Pi |
| **Logging** | SQLite + CSV export | Reproducible thesis data, easy charts |
| **Service management** | **systemd** (3 services, auto-start, auto-restart) | Production-grade, panel-impressive |
| **UI launch** | **Chromium kiosk mode** auto-launch on boot | Power on → dashboard live in 30s |
| **Camera** | **USB cam** (NOT CSI/picamera2) | User has USB cam, simpler code |
| **Web framework** | Flask + Flask-SocketIO | Lightweight, real-time |
| **GPIO library** | `gpiozero` + `lgpio` | Pi 5 RP1 chip compatible (RPi.GPIO is broken) |
| **DHT22 library** | `adafruit-circuitpython-dht` | Maintained, Pi 5 compatible (Adafruit_DHT is broken) |
| **Config** | YAML in `config/settings.yaml` | No hardcoded values anywhere |
| **OS** | Debian 13 Trixie (already installed) | Latest Pi OS base |
| **Python** | 3.13 (system default) | No pyenv needed |

---

## 🏗️ Architecture: 5-Layer Design

**Strict separation of concerns. Each layer talks ONLY to the layer directly below it (or via the event bus).**

```
┌─────────────────────────────────────────────┐
│ Layer 4: Web Interface (Flask + WebSocket)  │  ← user sees this
├─────────────────────────────────────────────┤
│ Layer 3: Application Logic (orchestrator)   │  ← the brain
├─────────────────────────────────────────────┤
│ Layer 2: Core Services (detector, sensors)  │  ← stateless workers
├─────────────────────────────────────────────┤
│ Layer 1: Hardware Abstraction (camera, GPIO)│  ← pure I/O wrappers
└─────────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────────┐
│ Layer 5: Persistence (SQLite, config, models)│ ← cross-cutting
└─────────────────────────────────────────────┘
```

### Layer responsibilities

**Layer 1 (`hardware/`):** Pure I/O. Knows nothing about YOLO, Flask, or business logic.
- `camera.py` — USB cam wrapper using `cv2.VideoCapture`
- `gpio.py` — GPIO setup using `gpiozero` (Pi 5 RP1 chip)
- `sensors.py` — DHT22 readers with retry logic + caching

**Layer 2 (`services/`):** Stateless workers. Take input, return output.
- `detector.py` — NCNN model inference, returns detections
- `sensor_reader.py` — DHT22 polling loop, publishes to event bus
- `classifier.py` — applies sorting rules, increments counters

**Layer 3 (`app/`):** The brain. Coordinates everything.
- `orchestrator.py` — starts services, manages frame pipeline
- `state.py` — single source of truth (counts, sensor readings)
- `events.py` — in-memory pub/sub bus

**Layer 4 (`api/`):** Web interface. Only talks to Layer 3.
- `server.py` — Flask app factory
- `routes.py` — REST endpoints
- `websocket.py` — real-time updates
- `templates/dashboard.html` — single-page UI

**Layer 5 (`persistence/`):** Data storage.
- `database.py` — SQLite connection + schema
- `models.py` — `Detection`, `SensorReading`, `SystemEvent` dataclasses
- `exporter.py` — CSV export for thesis analysis

---

## 📁 File structure (already created)

```
~/tomato-sorter/
├── CLAUDE.md                   ← THIS FILE (you're reading it)
├── ARCHITECTURE.md             ← Detailed architecture doc
├── README.md                   ← (to be created)
├── pyproject.toml              ← (to be created)
├── config/
│   └── settings.yaml           ← (to be created)
├── src/
│   └── tomato_sorter/
│       ├── __init__.py         ← (to be created)
│       ├── main.py             ← Entry point, CLI dispatcher
│       ├── hardware/
│       │   ├── __init__.py
│       │   ├── camera.py       ← USB cam (cv2.VideoCapture)
│       │   ├── gpio.py
│       │   └── sensors.py      ← DHT22 with adafruit-circuitpython-dht
│       ├── services/
│       │   ├── __init__.py
│       │   ├── detector.py     ← NCNN inference
│       │   ├── sensor_reader.py
│       │   └── classifier.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── orchestrator.py
│       │   ├── state.py
│       │   └── events.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── server.py
│       │   ├── routes.py
│       │   ├── websocket.py
│       │   └── templates/
│       │       └── dashboard.html
│       └── persistence/
│           ├── __init__.py
│           ├── database.py
│           ├── models.py
│           └── exporter.py
├── models/                     ← NCNN model files (download separately)
├── data/
│   └── logs/
├── scripts/
│   ├── install.sh
│   ├── test_camera.py
│   ├── test_sensors.py
│   ├── export_csv.py
│   └── benchmark.py
├── deploy/
│   ├── tomato-detector.service
│   ├── tomato-sensors.service
│   ├── tomato-dashboard.service
│   └── kiosk-autostart.sh
└── tests/
```

---

## 🔧 Hardware setup

| Component | Details |
|---|---|
| **Pi 5 model** | Raspberry Pi 5 Model B Rev 1.1, 8GB RAM (revision `d04171`) |
| **OS** | Debian 13 Trixie (kernel via `uname -a`) |
| **Storage** | 32GB SD card (~15GB free after setup) |
| **Camera** | **USB camera** at `/dev/video0` — use `cv2.CAP_V4L2` backend |
| **DHT22 #1** | RIPE bin — Pi GPIO 4 (physical pin 7), 3.3V power — wired and tested |
| **DHT22 #2** | UNRIPE bin — Pi GPIO 23 (physical pin 16), 3.3V power — wired and tested |
| **Servo 1 (gate)** | Arduino pin 9 — calibrated: closed=0°, open=50° |
| **Servo 2 (sorter)** | Arduino pin 10 — calibrated: left=145° (ripe), center=95° (unripe), right=50° (rotten) |
| **IR sensor** | Arduino pin 2 (interrupt) — wired and tested, triggers correctly |
| **Relay 1 + Fan 1** | Bin 1 (ripe) — Arduino pin 4 — relay clicks + fan spins confirmed |
| **Relay 2 + Fan 2** | Bin 2 (unripe) — Arduino pin 7 — relay clicks + fan spins confirmed |
| **Note: Relay module is 12V coil** | VCC = Arduino 5V (signal), JD-VCC = 12V supply (coils via breadboard rail), GND shared |
| **Fan wiring** | 12V (+) → COM, NO → Fan red, Fan black → 12V (−) (back to supply via breadboard) |
| **7-inch DSI display** | Pi's main screen — DSI cable + 5V/GND on pins 4/6. This IS the kiosk dashboard display. NOT a separate LCD component. |
| **Arduino Uno** | Connected to Pi via USB — handles servos, IR sensor, relays. Pi serial: `/dev/ttyACM0` |
| **5V PSU (external)** | Powers Servo 1 + Servo 2 via breadboard. NOT from Pi 5V pin. |
| **12V PSU** | Powers conveyor (via BTS7960) + fans (via relay load side) |
| **Cooling** | Active cooler RECOMMENDED (sustained YOLO inference heats CPU) |
| **Network** | WiFi at `192.168.100.23` (current session) |

> **GPIO pins TBD** — Killua will provide pin assignments. Update this table when confirmed.
> **No separate I2C/parallel LCD** — the 7-inch DSI display is the Pi's monitor. Dashboard shows there via Chromium kiosk.

### Bins

| Bin | Class | DHT22 | Fan |
|---|---|---|---|
| Bin 1 | Ripe | Yes | Yes (Relay 1) |
| Bin 2 | Unripe | Yes | Yes (Relay 2) |
| Bin 3 | Rotten | No | No |

### Pi 5 GPIO gotcha

Pi 5 uses RP1 chip — **`RPi.GPIO` library is BROKEN**, must use `gpiozero` + `lgpio`. The old Pi 4 code that imported `RPi.GPIO` will not work.

### DHT22 reliability note

DHT22 sensors have **40-60% read failure rate** (normal). Always implement caching — return last good value if read fails. Show in UI: real vs cached badge.

---

## 🔄 Sorting cycle (locked-in logic)

```
Servo 1 opens → 1 tomato drops on conveyor → Servo 1 closes fast
        ↓
Conveyor runs
        ↓
Camera detects tomato → logs class: ripe / unripe / rotten
        ↓
IR sensor triggers (tomato reached sort point)
        ↓
Servo 2 rotates: left=ripe, center=unripe, right=rotten
(uses last camera detection; fallback = unripe if no detection)
        ↓
Wait ~600ms (tomato falls into bin)
        ↓
Servo 2 returns to home position
        ↓
Servo 1 opens → next tomato → repeat
```

**Key rule:** Only 1 tomato on the conveyor at a time. Servo 1 only opens after Servo 2 has finished sorting the previous tomato.

---

## 📊 SQLite schema

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    class TEXT NOT NULL,           -- 'ripe', 'unripe', or 'rotten'
    confidence REAL NOT NULL,
    bbox_x INTEGER, bbox_y INTEGER,
    bbox_w INTEGER, bbox_h INTEGER,
    sorted_to INTEGER              -- bin number: 1=ripe, 2=unripe, 3=rotten
);

CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    container TEXT NOT NULL,       -- 'ripe' or 'unripe' (bin 3 has no sensor)
    temperature REAL,
    humidity REAL,
    is_cached INTEGER DEFAULT 0
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

---

## 🖥️ Dashboard design requirements (locked-in)

- **Style:** Industrial/SCADA-inspired. Clean, dark or neutral theme. No rainbow gradients, no nav accent bars, no AI slop animations.
- **Layout:**
  - Live camera feed (top center)
  - Bin counters: Bin 1 (Ripe), Bin 2 (Unripe), Bin 3 (Rotten) — large numbers
  - Gauges: temperature + humidity for Bin 1 and Bin 2 (DHT22)
  - Status row: Conveyor ON/OFF, Fan 1 ON/OFF, Fan 2 ON/OFF, Servo states
  - Activity log: last 10 detections with timestamp + class + confidence
- **Tech:** Flask + Flask-SocketIO for real-time push. Single HTML page, no frameworks (vanilla JS or minimal).
- **Real-time:** WebSocket pushes state every ~500ms. No polling.

---

## 📍 Current progress

### ✅ Completed
- [x] Pi 5 setup verified (8GB, Trixie, ~15GB free)
- [x] VNC enabled and working
- [x] VS Code Remote-SSH connected (`192.168.100.23`)
- [x] Project folder at `~/tomato-sorter`, git initialized
- [x] Full directory structure created
- [x] Claude Code installed
- [x] CLAUDE.md + ARCHITECTURE.md written
- [x] System packages installed (apt — Trixie compatible)
- [x] Python venv created (`.venv --system-site-packages`)
- [x] `pyproject.toml` written, all deps installed (674MB venv, no CUDA bloat)
- [x] NCNN model converted from `best.pt` — 3 classes: ripe, unripe, rotten
- [x] Camera verified working at `/dev/video0` (640x480, V4L2 backend)
- [x] NCNN inference verified — model loads, output shape (7, 4725) confirmed
- [x] `scripts/test_camera.py` — MJPEG stream at port 8080, live detection working
- [x] Full sorting workflow designed and locked in (see Sorting Cycle section)
- [x] Dashboard requirements locked in
- [x] Arduino IDE + arduino-cli installed (uploads from Pi terminal)
- [x] Arduino Uno (CH340 clone) on `/dev/ttyUSB0`, serial comms verified
- [x] Servo 1 (gate) calibrated: closed=0°, open=50°
- [x] Servo 2 (sorter) calibrated: left=145°, center=95°, right=50°
- [x] IR sensor wired (Arduino pin 2), triggers correctly
- [x] Dual relay module (12V coil) wired + clicks on command
- [x] Both fans spin via relay (or default ON at Arduino boot)
- [x] Both DHT22 sensors reading reliably (Pi GPIO 4 + 23, 3.3V)
- [x] **Final production firmware** uploaded — `arduino/sketches/tomato_sorter`
  - One sketch handles all hardware
  - Fans default ON at boot
  - Full serial protocol implemented
  - Calibrated angles baked in

### ⏳ Next steps (in order)

1. **GPIO pin assignment** — Killua to provide pin numbers for: Servo 1, Servo 2, IR sensor, Relay 1, Relay 2. Update hardware table above.

2. **Layer 1 implementation** — hardware abstraction:
   - `hardware/camera.py` — USB cam wrapper (cv2.CAP_V4L2)
   - `hardware/sensors.py` — DHT22 x2 with caching
   - `hardware/gpio.py` — Servo 1, Servo 2, IR sensor, Relay 1, Relay 2 (gpiozero)

3. **Layer 5 implementation** — `persistence/database.py`, `models.py`, `exporter.py`

4. **Layer 2 implementation** — `services/detector.py` (NCNN), `sensor_reader.py`, `classifier.py`

5. **Layer 3 implementation** — `app/orchestrator.py` (full sorting cycle logic), `state.py`, `events.py`

6. **Layer 4 implementation** — Flask dashboard (SCADA-style UI, WebSocket, MJPEG feed)

7. **`config/settings.yaml`** — GPIO pins, thresholds, timing values (servo delays, IR debounce)

8. **systemd services** — 3 services: detector, sensors, dashboard

9. **Chromium kiosk autostart** — `~/.config/wayfire.ini`

10. **Stress test** — 1-hour run before defense

---

## 🛡️ Risk register

| Risk | Mitigation |
|---|---|
| DHT22 reads fail (40-60% normal) | Caching layer, UI badge shows cached vs real |
| Pi overheats during long demos | Active cooler, throttling alarm in UI |
| Service crashes mid-defense | systemd auto-restart |
| SD card corruption | Regular DB backups, NVMe SSD upgrade if budget |
| YOLO inference too slow | NCNN already optimized; can drop to 320x320 if needed |
| WiFi drops on demo day | Fully local — `localhost` dashboard, no internet needed |

---

## 🚫 Anti-patterns to avoid (lessons from Pi 4 v1)

1. **No multiple scripts doing the same thing.** One DHT22 reader. One YOLO detector. Period.
2. **No hardcoded values in code.** Everything in `config/settings.yaml`.
3. **No `print()` debugging.** Use Python `logging` module with file rotation.
4. **No mixing concerns.** Sensor logic doesn't import Flask. Web routes don't touch GPIO directly.
5. **No `RPi.GPIO`.** Use `gpiozero` + `lgpio` for Pi 5.
6. **No `Adafruit_DHT`.** Use `adafruit-circuitpython-dht`.
7. **No models in git.** Models are downloaded/copied separately. Add `models/*.bin`, `models/*.param` to `.gitignore`.
8. **No dataset in repo.** Training data lives elsewhere (Google Drive, external drive).

---

## 💡 Defense-day talking points

When the panel asks about the system, the user should be able to confidently say:

> *"The system follows a 5-layer architecture with strict separation of concerns. Three systemd services handle detection, sensing, and the web interface independently — each can fail and recover without affecting the others. Configuration is externalized to YAML, all events are logged to SQLite for reproducible analysis, and the system auto-launches in kiosk mode for unattended operation."*

This is panel-grade architecture. Build toward this story.

---

## 🤝 How Claude Code should work with the user

1. **Be a teacher, not just a coder.** Killua wants to learn the patterns, not just get working code. Explain *why* you chose an approach.
2. **Show your work.** When implementing a module, briefly state what it does, what dependencies it needs, and what tests verify it.
3. **Test as you go.** After each module, write a small test script in `scripts/` that proves it works on the actual hardware.
4. **Stay in Taglish when casual, English when technical.** Don't force it either way.
5. **Push back honestly.** If Killua suggests something that conflicts with the architecture, say so directly.
6. **One layer at a time.** Don't jump ahead. Layer 1 → Layer 5 → Layer 2 → Layer 3 → Layer 4 (this order means hardware is testable first, then persistence, then logic, then UI).
7. **Reference this file often.** When in doubt, re-read the locked-in decisions section.

---

## 📚 Reference docs

- `ARCHITECTURE.md` — full architecture doc (in this same directory)
- Original Pi 4 repo: `https://github.com/imove0n/RASPI-4-SORTING-PROJECT4`
- Pi 5 GPIO docs: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header
- gpiozero docs: https://gpiozero.readthedocs.io/
- adafruit-circuitpython-dht: https://docs.circuitpython.org/projects/dht/

---

**End of CLAUDE.md** — Last updated: April 27, 2026

Model: YOLO11n, 3 classes (ripe/unripe/rotten), 480x480, NCNN format, 10MB weights.
Camera: USB at /dev/video0, V4L2 backend, 640x480.
Venv: .venv --system-site-packages, 674MB, no CUDA.

Let's build a thesis-defense-grade tomato sorter. Direct, no fluff, production-quality.
