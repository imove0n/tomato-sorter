# Tomato Sorter v2.0 — Master Cheatsheet

Everything you need in one place. Pin diagrams, commands, debugging, restart procedures.

---

## 1. Quick Start

```bash
cd ~/tomato-sorter
.venv/bin/python -m tomato_sorter.main
```

Wait ~25 seconds for YOLO to warm up. Then open Chromium → `http://localhost:5000`

**Stop:** `Ctrl+C`
**Run in background:** `nohup .venv/bin/python -m tomato_sorter.main > /tmp/sorter.log 2>&1 &`
**Kill background:** `kill $(pgrep -f tomato_sorter.main)`

---

## 2. Pin Assignments

### Pi 5 GPIO (40-pin header)

```
Function          BCM GPIO    Physical Pin   Notes
─────────────────────────────────────────────────────────────
Pi 5V (rail)         —          Pin 2/4      external loads
Pi GND (rail)        —          Pin 6/9/14   common ground
DHT22 #1 RIPE       4           Pin 7        3.3V power
DHT22 #2 UNRIPE     23          Pin 16       3.3V power
DHT22 VCC           —           Pin 1/17     3.3V (NOT 5V)
DHT22 GND           —           Pin 6/14     ground
USB Camera          —           USB port     /dev/video0 (auto)
Arduino Uno         —           USB port     /dev/ttyUSB0
BTS7960 control     —           Pin 2,4,6,9  via breadboard
```

### Arduino Uno

```
Function          Arduino Pin   Type      Notes
─────────────────────────────────────────────────────────────
Servo 1 (gate)        D9        PWM       calibrated 0=closed, 50=open
Servo 2 (sorter)      D10       PWM       LEFT=122 (ripe), CENTER=90 (unripe), RIGHT=55 (rotten)
IR sensor             D2        Interrupt edge-triggered
Relay 1 (Fan 1)       D4        Output    active LOW
Relay 2 (Fan 2)       D7        Output    active LOW
USB Serial            —         USB-B     to Pi /dev/ttyUSB0 @ 9600 baud
```

### BTS7960 Motor Driver (conveyor)

```
BTS7960 Pin    Wire to                Notes
────────────────────────────────────────────────────────────
RPWM           Pi 5V                  pinned HIGH = full speed
R_EN           Pi 5V                  always enabled forward
LPWM           Pi GND                 reverse off
L_EN           Pi GND                 reverse off
VCC            Pi 5V                  logic power
GND            Pi GND                 common ground
B+             12V supply (+)         motor power
B-             12V supply (-)         motor ground
M+             Conveyor motor wire    swap M+/M- if backwards
M-             Conveyor motor wire
```

### Dual Relay Module

```
Relay Pin           Wire to             Notes
─────────────────────────────────────────────────────────
VCC                 Arduino 5V          signal/LED power
GND                 Arduino GND         signal ground
JD-VCC              12V supply (+)      coil power (12V module!)
IN1                 Arduino D4          Fan 1 control
IN2                 Arduino D7          Fan 2 control
COM1                12V supply (+)      Fan 1 power in
NO1                 Fan 1 red wire      Fan 1 switched output
COM2                12V supply (+)      Fan 2 power in
NO2                 Fan 2 red wire      Fan 2 switched output
NC1, NC2            empty               not used
Fan 1 black         12V supply (-)      return path
Fan 2 black         12V supply (-)      return path
```

---

## 3. Power Supplies

| Source             | Powers                                              |
|--------------------|-----------------------------------------------------|
| Pi USB-C 5V/5A     | Raspberry Pi 5 only                                 |
| 5V PSU (2A+)       | Servo 1, Servo 2 (via Breadboard 2)                 |
| 12V supply #1      | Conveyor motor (via BTS7960 B+/B-)                  |
| 12V supply #2      | Relay coils (JD-VCC) + fans (via COM/NO)            |
| Pi 5V GPIO pin     | DHT22, IR sensor, relay logic VCC, BTS7960 logic    |
| Pi USB-A           | Arduino Uno (powers + serial communication)         |

**ALL grounds tied together** = single common ground reference (critical).

---

## 4. Calibrated Values

`config/servo_angles.json`:
```json
{
  "closed": 0,    // gate fully closed
  "open": 50,     // gate open enough for 1 tomato
  "left":  122,   // sorter -> ripe bin
  "center": 90,   // sorter -> unripe bin (rest)
  "right": 55     // sorter -> rotten bin
}
```

`config/settings.yaml` key timings:
```yaml
gate_open_hold_ms:    300    # gate stays open
min_travel_ms:        1500   # ignore IR before this (anti-false-trigger)
conveyor_travel_ms:   6000   # max wait for IR before timeout
sort_settle_ms:       2500   # Servo 2 holds sort position
rest_between_ms:      300    # idle between cycles
fallback_class:       unripe # used if camera missed but IR fired
```

---

## 5. File Layout

```
~/tomato-sorter/
├── CLAUDE.md                          ← project context (auto-loaded)
├── CHEATSHEET.md                      ← this file
├── ARCHITECTURE.md
├── DOCUMENTATION.md                   ← thesis-style document
├── config/
│   ├── settings.yaml                  ← all tunable values
│   └── servo_angles.json              ← calibration
├── arduino/sketches/
│   ├── tomato_sorter/                 ← FINAL PRODUCTION FIRMWARE
│   ├── serial_test/                   ← serial comms test
│   ├── servo_calibrate/               ← Servo 1 calibration
│   ├── servo2_calibrate/              ← Servo 2 calibration
│   ├── ir_test/                       ← IR sensor test
│   └── relay_test/                    ← relay test
├── src/tomato_sorter/                 ← Pi-side Python app
│   ├── main.py                        ← entry point
│   ├── config.py                      ← loads settings.yaml
│   ├── arduino_link.py                ← serial wrapper
│   ├── sensors.py                     ← DHT22 polling
│   ├── detector.py                    ← camera + YOLO inference
│   ├── orchestrator.py                ← sort cycle FSM
│   ├── server.py                      ← Flask + REST API
│   ├── state.py                       ← shared state
│   ├── database.py                    ← SQLite logger
│   └── templates/dashboard.html       ← SCADA UI
├── scripts/                           ← debug + calibration tools
│   ├── test_camera.py                 ← MJPEG stream + YOLO
│   ├── test_dht22.py                  ← DHT22 standalone test
│   ├── camera_viewer.py               ← cv2 window viewer
│   ├── servo_calibrate.py             ← Servo 1 dial-in
│   ├── servo2_calibrate.py            ← Servo 2 dial-in
│   ├── ir_test.py                     ← IR live monitor
│   └── build_documentation_pdf.py     ← generates PDF doc
├── models/
│   ├── best.ncnn.bin / .param         ← (broken NCNN — not used)
│   └── my_model11n480/train/weights/best.pt   ← active model
├── data/sorter.db                     ← SQLite database
└── .venv/                              ← Python virtual env
```

---

## 6. API Endpoints (when dashboard is running)

| Method | Endpoint                      | What                                      |
|--------|-------------------------------|-------------------------------------------|
| GET    | `/`                           | the dashboard HTML                        |
| GET    | `/stream`                     | MJPEG live camera feed (with detection boxes) |
| GET    | `/api/state`                  | full system state (sensors, counts, IR, etc.) |
| GET    | `/api/detections`             | what camera currently sees                |
| GET    | `/api/arduino/inbox`          | last 20 messages from Arduino             |
| POST   | `/api/start`                  | start auto sort cycle                     |
| POST   | `/api/stop`                   | stop auto sort cycle                      |
| POST   | `/api/reset`                  | clear all bin counts and history          |
| POST   | `/api/manual/gate_open`       | manual: open gate                         |
| POST   | `/api/manual/gate_close`      | manual: close gate                        |
| POST   | `/api/manual/sort_ripe`       | manual: Servo 2 → LEFT                    |
| POST   | `/api/manual/sort_unripe`     | manual: Servo 2 → CENTER                  |
| POST   | `/api/manual/sort_rotten`     | manual: Servo 2 → RIGHT                   |
| POST   | `/api/manual/fan1_on/off`     | toggle Fan 1                              |
| POST   | `/api/manual/fan2_on/off`     | toggle Fan 2                              |

Quick API tests from terminal:

```bash
curl -s http://localhost:5000/api/state | python3 -m json.tool
curl -X POST http://localhost:5000/api/start
curl -X POST http://localhost:5000/api/stop
curl -X POST http://localhost:5000/api/reset
curl -X POST http://localhost:5000/api/manual/sort_ripe
```

---

## 7. Pi ↔ Arduino Serial Protocol

USB serial @ 9600 baud, newline-terminated commands.

**Pi → Arduino:**
```
SERVO1:OPEN          gate opens
SERVO1:CLOSE         gate closes
SERVO2:LEFT          sort to ripe bin    (122°)
SERVO2:CENTER        sort to unripe bin  (90°)
SERVO2:RIGHT         sort to rotten bin  (55°)
RELAY1:ON / OFF      Fan 1 control
RELAY2:ON / OFF      Fan 2 control
PING                 returns PONG
STATUS               returns full state
```

**Arduino → Pi (async):**
```
IR:TRIGGERED         tomato detected at sort point
IR:CLEAR             tomato passed
SERVO1:DONE          gate movement complete
SERVO2:DONE          sorter movement complete
READY                boot complete
```

---

## 8. Debugging — Common Problems

### "Servos don't move from dashboard"

**Most common cause:** wrong firmware on Arduino.

After calibrating, you need to flash the **production firmware** back. Check the Arduino's boot banner via the inbox:

```bash
curl -s http://localhost:5000/api/arduino/inbox | python3 -m json.tool | head -8
```

Look for the FIRST line. It should say:
- ✅ `BOOT: gate=0 sorter=90 relay1=ON relay2=ON` → production firmware (correct)
- ❌ `BOOT: Servo calibrate ready (pin 9)` → Servo 1 calibration sketch (wrong!)
- ❌ `BOOT: Servo 2 calibrate ready (pin 10)` → Servo 2 calibration sketch (wrong!)
- ❌ `BOOT: IR sensor test ready` → IR test sketch (wrong!)

If it's wrong, re-upload production firmware:
```bash
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/tomato_sorter
```

Then refresh dashboard.

### "App won't start"

```bash
# Check if already running
pgrep -f tomato_sorter.main

# Kill stale process
kill $(pgrep -f tomato_sorter.main)
fuser -k /dev/video0 /dev/video1 /dev/ttyUSB0 2>/dev/null

# Check logs
tail -30 /tmp/sorter.log
```

### "Camera not opening / black"

```bash
# Find which video device the camera is on
ls /dev/video*
v4l2-ctl --list-devices

# Test camera directly
fswebcam -d /dev/video0 -r 640x480 --no-banner /tmp/test.jpg

# Free a stuck camera
fuser -k /dev/video0
```

### "DHT22 not reading"

```bash
# Stop dashboard first (it holds the GPIO)
kill $(pgrep -f tomato_sorter.main)

# Run standalone test
.venv/bin/python scripts/test_dht22.py
```

If "DHT sensor not found" → physical wiring issue. Check VCC=3.3V (NOT 5V), DATA pin, GND.

### "Arduino not connecting"

```bash
# Find Arduino port
ls /dev/ttyUSB* /dev/ttyACM*
lsusb | grep -i serial    # CH340 clones show as "QinHeng Electronics"

# Check user is in dialout group (needed for serial access)
groups bacadasa | grep dialout

# Test connection
.venv/bin/python -c "
import serial, time
a = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
time.sleep(2)
a.write(b'PING\n')
print(a.readline().decode())
"
```

### "Servo doesn't move"

1. Check 5V PSU is plugged in
2. Verify common ground (servo PSU GND ↔ Arduino GND)
3. Reseat signal wire on Arduino pin 9 or 10
4. Run servo manual test:
   ```bash
   curl -X POST http://localhost:5000/api/manual/sort_ripe
   ```

### "Relay clicks but fans don't spin"

JD-VCC needs 12V (this module is 12V coil). Check JD-VCC connection.

If you want fans always-on regardless of relay, just direct connect:
- Fan red → 12V (+)
- Fan black → 12V (−)

### "IR sensor false-triggers / doesn't trigger"

Adjust the **blue trim potentiometer** on the IR module. Turn slowly with a screwdriver.

```bash
# Watch IR live (dashboard must be running)
curl -s http://localhost:5000/api/arduino/inbox | python3 -m json.tool | grep IR
```

### "Browser shows 0 / no updates"

1. Hard refresh: `Ctrl+Shift+R`
2. Check API directly: `curl http://localhost:5000/api/state`
3. Open DevTools (F12) → Console → look for JS errors
4. Common JSON errors: `Infinity` not allowed (we fixed this — make sure latest code)

### "Dashboard says IDLE but cycle is running"

Browser cached old state. **Hard refresh.**

### "Cycle hits timeout / no IR"

The IR sensor isn't catching the tomato. Check:
1. IR sensor positioned at end of conveyor
2. Trim pot adjusted for sensitivity
3. Tomato actually reaches the sensor (conveyor speed OK)

### "Camera misses detection (conf=0.0 fallback)"

YOLO too slow (2 FPS) for fast-moving tomatoes. Solutions:
1. Slow down conveyor
2. Position camera to see tomato longer
3. Improve lighting

---

## 9. Calibration Workflow

> ⚠️ **CRITICAL — read this first:** The Arduino can only run ONE sketch at a time.
> The calibration sketches accept `A:90` / `B:90` commands.
> The production firmware accepts `SERVO1:OPEN` / `SERVO2:LEFT` commands.
> **They are NOT interchangeable.**
>
> The dashboard ONLY works with the **production firmware** (`tomato_sorter`).
> If the calibration sketch is on the Arduino, the dashboard will fail silently —
> servos won't move, cycle won't sort, you'll see "UNKNOWN" responses in the logs.
>
> **Always re-upload `arduino/sketches/tomato_sorter` after any calibration session.**

### Workflow: switching between firmware

| What you want to do | Sketch on Arduino       | Tool to use                        |
|---------------------|-------------------------|-------------------------------------|
| Use the dashboard   | `tomato_sorter`         | `python -m tomato_sorter.main`     |
| Calibrate Servo 1   | `servo_calibrate`       | `python scripts/servo_calibrate.py` |
| Calibrate Servo 2   | `servo2_calibrate`      | `python scripts/servo2_calibrate.py`|
| Test IR alone       | `ir_test`               | `python scripts/ir_test.py`         |
| Test relay alone    | `relay_test`            | (manual via serial)                 |

### Quick "back to production" command

After any calibration, run this to flash the production firmware back:

```bash
cd ~/tomato-sorter
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/tomato_sorter
```

Then start the dashboard:
```bash
.venv/bin/python -m tomato_sorter.main
```

### Recalibrate Servo 1 (gate)

```bash
# Stop dashboard
kill $(pgrep -f tomato_sorter.main)

# Upload calibration sketch
cd ~/tomato-sorter
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/servo_calibrate

# Run interactive tool
.venv/bin/python scripts/servo_calibrate.py
# Type angles 0-180, save 'open' and 'closed' positions, quit
```

### Recalibrate Servo 2 (sorter)

```bash
# Upload Servo 2 calibration sketch
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/servo2_calibrate

# Run tool
.venv/bin/python scripts/servo2_calibrate.py
# Save 'left', 'center', 'right' positions
```

### After ANY recalibration

Update the firmware constants and re-upload production sketch:

```bash
# Edit angles in arduino/sketches/tomato_sorter/tomato_sorter.ino
# (GATE_OPEN, SORT_LEFT, SORT_CENTER, SORT_RIGHT)

# Recompile and upload
cd ~/tomato-sorter
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/tomato_sorter

# Restart dashboard
.venv/bin/python -m tomato_sorter.main
```

---

## 10. Database Queries

```bash
# Open the DB
sqlite3 ~/tomato-sorter/data/sorter.db

# Useful queries:
.tables
SELECT class, COUNT(*) FROM detections GROUP BY class;
SELECT * FROM detections ORDER BY id DESC LIMIT 10;
SELECT * FROM sensor_readings WHERE container='ripe' ORDER BY id DESC LIMIT 10;
SELECT * FROM system_events WHERE level='warning' OR level='error' ORDER BY id DESC LIMIT 20;

# Export to CSV
.headers on
.mode csv
.output detections.csv
SELECT * FROM detections;
.output stdout
.quit
```

---

## 11. Sorting Cycle (locked-in workflow)

```
[CLICK START]
    ↓
Servo 1 OPEN (gate) → tomato drops → Servo 1 CLOSE
    ↓
[Conveyor moves continuously]
    ↓
Camera + YOLO classifies tomato (logs ripe/unripe/rotten)
    ↓
Tomato reaches end → IR sensor triggers
    ↓
ONLY THEN: Servo 2 rotates based on classification:
    LEFT (122°)  = ripe   → Bin 1
    CENTER (90°) = unripe → Bin 2
    RIGHT (55°)  = rotten → Bin 3
    ↓
Servo 2 holds for 2.5s (tomato falls into bin)
    ↓
Servo 2 returns to CENTER
    ↓
Repeat from Servo 1 OPEN
```

**Safety:** if IR doesn't trigger within 6 seconds, Servo 2 does NOT move (no fallback sort).

---

## 12. Standalone Test Scripts

```bash
.venv/bin/python scripts/test_camera.py        # Camera + YOLO via MJPEG
.venv/bin/python scripts/test_dht22.py         # DHT22 sensor reads
.venv/bin/python scripts/ir_test.py            # IR sensor live monitor
.venv/bin/python scripts/servo_calibrate.py    # Servo 1 (gate) calibration
.venv/bin/python scripts/servo2_calibrate.py   # Servo 2 (sorter) calibration
.venv/bin/python scripts/camera_viewer.py      # cv2 window of dashboard stream
.venv/bin/python scripts/build_documentation_pdf.py   # generate thesis PDF
```

---

## 13. Boot-to-Demo Sequence

When everything is wired and configured:

1. **Plug in all power supplies** (12V x2, 5V, Pi USB-C)
2. **Pi boots** (~20s)
3. **Auto-login + dashboard auto-start** (configure systemd later)
4. **Chromium kiosk mode** opens to localhost:5000
5. **Click START on dashboard**
6. Demo runs autonomously

For now (until systemd is set up): start manually after boot.

---

## 14. Quick Health Check

```bash
curl -s http://localhost:5000/api/state | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('System State')
print('============')
print(f'  FPS:           {d[\"fps\"]}')
print(f'  Cycle:         {\"RUNNING\" if d[\"cycle_running\"] else \"IDLE\"}')
print(f'  Counts:        Bin1={d[\"counts\"][\"ripe\"]} Bin2={d[\"counts\"][\"unripe\"]} Bin3={d[\"counts\"][\"rotten\"]}')
print(f'  IR sensor:     {d[\"ir\"]}')
print(f'  Gate / Sorter: {d[\"gate\"]} / {d[\"sorter\"]}')
print(f'  Fans:          F1={\"ON\" if d[\"fan1_on\"] else \"OFF\"} F2={\"ON\" if d[\"fan2_on\"] else \"OFF\"}')
r = d['sensors']['ripe']; u = d['sensors']['unripe']
print(f'  DHT22 Ripe:    {r[\"temp\"]}°C / {r[\"hum\"]}% (cached={r[\"cached\"]})')
print(f'  DHT22 Unripe:  {u[\"temp\"]}°C / {u[\"hum\"]}% (cached={u[\"cached\"]})')
print(f'  Last event:    {d[\"last_event\"]}')
"
```

Save this as `scripts/health.sh` for quick checks.

---

## 15. Emergency Recovery

If everything is broken:

```bash
# Nuclear option — kill everything, free all devices
sudo pkill -9 python
sudo fuser -k /dev/video0 /dev/video1 /dev/ttyUSB0 /dev/ttyACM0
sudo fuser -k /dev/gpiochip0 2>/dev/null

# Check no processes left
pgrep -af python

# Re-upload firmware to known good
cd ~/tomato-sorter
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 \
  --fqbn arduino:avr:uno arduino/sketches/tomato_sorter

# Restart dashboard
.venv/bin/python -m tomato_sorter.main
```

---

**End of cheatsheet** — keep this open in another window during demos.
