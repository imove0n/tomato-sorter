# AI-Powered Tomato Sorting System v2.0

**Project Documentation — Thesis Prototype**

---

## 1. Project Overview

This system is an automated tomato sorting machine that uses computer vision and IoT sensors to classify tomatoes by ripeness condition and sort them into the correct storage bins automatically. The system runs on a Raspberry Pi 5 with a YOLO11n deep learning model and is supported by an Arduino Uno for real-time hardware control. A web-based dashboard provides live monitoring and control through a 7-inch touchscreen display.

The prototype is designed to demonstrate three things:
1. Real-time object detection on edge hardware (no cloud, no internet required)
2. Automated mechanical sorting based on AI classification
3. Continuous environmental monitoring of storage bins via dual DHT22 sensors

---

## 2. System Architecture

The system follows a 5-layer software architecture with strict separation of concerns:

| Layer | Purpose |
|---|---|
| Layer 1 — Hardware | Raw I/O wrappers (camera, GPIO, sensors) |
| Layer 2 — Services | Stateless workers (YOLO detector, sensor poller, classifier) |
| Layer 3 — Application | Orchestrator, state management, event bus |
| Layer 4 — Web Interface | Flask dashboard with real-time WebSocket updates |
| Layer 5 — Persistence | SQLite database, CSV export for analysis |

**Hardware split:**
- **Raspberry Pi 5** handles AI inference, web dashboard, sensor logging, and conveyor control
- **Arduino Uno** handles real-time servo control, IR sensor reading, and relay switching

The two communicate via USB serial (`/dev/ttyACM0`).

---

## 3. Complete Materials List

### 3.1 Main Processing Unit

| Component | Specification | Quantity |
|---|---|---|
| Raspberry Pi 5 | 8GB RAM, Debian 13 Trixie OS | 1 |
| 7-inch DSI Touchscreen Display | DSI cable + 5V/GND on pins 4 and 6 | 1 |
| MicroSD Card | 32GB | 1 |
| Pi 5 USB-C Power Adapter | 5V/5A official | 1 |
| Active Cooling Fan | For sustained CPU inference | 1 |

### 3.2 Microcontroller

| Component | Specification | Quantity |
|---|---|---|
| Arduino Uno | ATmega328P, hardware PWM control | 1 |
| USB-A to USB-B Cable | Pi to Arduino link (power + serial) | 1 |

### 3.3 Vision and AI

| Component | Specification | Quantity |
|---|---|---|
| USB Camera | 640×480 resolution, /dev/video0 | 1 |
| YOLO11n Model | NCNN format, 3 classes (ripe, unripe, rotten), 480×480 input | 1 |

### 3.4 Actuation

| Component | Specification | Quantity |
|---|---|---|
| Servo Motor (Gate) | Releases tomatoes one at a time | 1 |
| Servo Motor (Sorter) | 180° — left=ripe, center=unripe, right=rotten | 1 |
| BTS7960 Motor Driver | H-bridge for 12V DC conveyor | 1 |
| DC Conveyor Motor | 12V | 1 |

### 3.5 Sensing

| Component | Specification | Quantity |
|---|---|---|
| DHT22 Sensor | Temperature and humidity — Bin 1 (ripe) | 1 |
| DHT22 Sensor | Temperature and humidity — Bin 2 (unripe) | 1 |
| IR Sensor | Detects tomato at sort point | 1 |

### 3.6 Power Supply

| Component | Specification | Quantity |
|---|---|---|
| 12V Power Supply | Conveyor motor + fans | 1 |
| 5V Power Supply (2A min) | Servo 1 and Servo 2 | 1 |

### 3.7 Relay and Cooling

| Component | Specification | Quantity |
|---|---|---|
| Dual Relay Module | Controls Fan 1 and Fan 2 | 1 |
| DC Fan | Bin 1 ventilation (ripe) | 1 |
| DC Fan | Bin 2 ventilation (unripe) | 1 |

### 3.8 Wiring and Prototyping

| Component | Specification | Quantity |
|---|---|---|
| Breadboard | Full-size | 3 |
| Jumper Wires | Assorted M-M, M-F, F-F | 1 set |

### 3.9 Storage Bins

| Bin | Class | DHT22 | Fan |
|---|---|---|---|
| Bin 1 | Ripe | Yes | Yes |
| Bin 2 | Unripe | Yes | Yes |
| Bin 3 | Rotten | No | No |

---

## 4. Sorting Workflow

The complete operational cycle of the system:

```
1. Servo 1 (gate) opens briefly
2. One tomato falls onto the conveyor
3. Servo 1 closes quickly to prevent multiple tomatoes
4. Conveyor runs (12V motor via BTS7960)
5. USB camera captures tomato → YOLO11n classifies as ripe / unripe / rotten
6. Detection logged to SQLite database
7. IR sensor at end of conveyor detects tomato arrival
8. Pi commands Arduino to rotate Servo 2:
   - Left  = Ripe   → Bin 1
   - Center = Unripe → Bin 2
   - Right = Rotten → Bin 3
9. Servo 2 holds for ~600ms (tomato falls into bin)
10. Servo 2 returns to home position
11. Servo 1 opens again → next tomato → repeat
```

**Key safety rule:** Only one tomato is allowed on the conveyor at any time. Servo 1 only opens after Servo 2 has finished sorting the previous tomato.

---

## 5. Software Stack

| Software | Purpose |
|---|---|
| Python 3.13 | Main programming language on Pi |
| OpenCV (system, GTK/Qt5) | Camera capture and image preprocessing |
| NCNN | YOLO model inference (ARM-optimized, 2-3x faster than PyTorch) |
| Flask + Flask-SocketIO | Web server and real-time WebSocket updates |
| SQLite | Logging detections, sensor readings, system events |
| gpiozero + lgpio | Pi 5 GPIO control (RP1 chip compatible) |
| adafruit-circuitpython-dht | DHT22 sensor reading |
| pyserial | Pi to Arduino serial communication |
| Arduino IDE / C++ | Arduino Uno firmware |
| systemd | Auto-start, auto-restart of services on boot |
| Chromium | Kiosk-mode dashboard display |

---

## 6. Communication Protocol (Pi ↔ Arduino)

The Pi sends commands to the Arduino over USB serial at 9600 baud:

**Pi → Arduino:**
| Command | Action |
|---|---|
| `SERVO1:OPEN` | Gate opens to release one tomato |
| `SERVO1:CLOSE` | Gate closes |
| `SERVO2:LEFT` | Sort to ripe bin |
| `SERVO2:CENTER` | Sort to unripe bin |
| `SERVO2:RIGHT` | Sort to rotten bin |
| `RELAY1:ON` / `RELAY1:OFF` | Fan 1 control |
| `RELAY2:ON` / `RELAY2:OFF` | Fan 2 control |

**Arduino → Pi:**
| Message | Meaning |
|---|---|
| `IR:TRIGGERED` | Tomato detected at sort point |
| `SERVO1:DONE` | Gate movement complete |
| `SERVO2:DONE` | Sorter movement complete |
| `OK` | Generic acknowledgement |

---

## 7. Dashboard Features

The web dashboard runs in Chromium kiosk mode on the 7-inch DSI display and is accessible at `http://localhost:5000`:

- **Live camera feed** with detection bounding boxes overlaid in real-time
- **Bin counters** showing current totals for Bin 1 (Ripe), Bin 2 (Unripe), and Bin 3 (Rotten)
- **Environmental gauges** showing temperature and humidity per bin
- **System status indicators** for conveyor, fans, and servo positions
- **Manual controls** to toggle fans on/off and run servo calibration
- **Activity log** showing the last 10 detections with timestamps and confidence values

The interface follows an industrial SCADA design pattern — clean, neutral dark theme with no decorative animations, suitable for unattended kiosk operation.

---

## 8. Power Distribution

The system uses three independent power sources, all sharing a common ground:

| Power Source | Powers |
|---|---|
| Pi USB-C Adapter (5V/5A) | Raspberry Pi 5 |
| 12V Power Supply | Conveyor motor (via BTS7960), fans (via relay load side) |
| 5V Power Supply (2A+) | Servo 1 and Servo 2 |
| Pi 5V GPIO pin | DHT22 sensors, IR sensor, relay control logic |
| Pi USB to Arduino | Arduino Uno (also provides serial communication) |

This separation prevents brown-outs on the Pi caused by motor/servo current spikes.

---

## 9. Reliability Features

| Risk | Mitigation |
|---|---|
| DHT22 read failures (40-60% normal) | Caching layer — UI shows real vs cached values |
| Pi CPU overheating | Active cooler + thermal alarm in dashboard |
| Service crashes during operation | systemd auto-restart on failure |
| Camera misses detection | Fallback class = unripe (safe default) |
| Network failure | Fully local operation — no internet required |
| Power-on demo | Boot to fullscreen dashboard in ~30 seconds |

---

## 10. Boot Sequence

When the Pi is powered on, the following happens automatically:

1. Debian Trixie boots and auto-logs in as user `bacadasa`
2. Three systemd services start in order:
   - `tomato-sensors.service` — DHT22 polling loop
   - `tomato-detector.service` — Camera + YOLO inference
   - `tomato-dashboard.service` — Flask web server
3. Wayfire compositor launches the desktop
4. Chromium opens automatically in fullscreen kiosk mode at `http://localhost:5000`
5. Dashboard is fully operational

Total boot-to-dashboard time: approximately 30 seconds.

---

## End of Documentation

Project: Tomato Sorter v2.0
Hardware: Raspberry Pi 5 + Arduino Uno
Date: April 2026
