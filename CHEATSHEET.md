# Tomato Sorter v2.0 — Cheatsheet

Current machine truth as of this repo state.

## 1. Quick Start

```bash
cd ~/tomato-sorter
.venv/bin/python -m tomato_sorter.main
```

Open the dashboard at:

```text
http://localhost:5000
```

Stop:

```bash
Ctrl+C
```

## 2. Current Hardware Map

### Raspberry Pi 5

```text
Function                  BCM    Physical Pin
Pi 5V rail                 -     2 or 4
Pi GND rail                -     6 / 9 / 14 / 20 / 25 / 30 / 34 / 39
DHT22 ripe                 4     7
DHT22 unripe              23     16
BTS RPWM                  18     12
BTS LPWM                  19     35
Arduino Uno over USB       -     /dev/ttyUSB0
```

### Arduino Uno

```text
Function                  Pin    Notes
IR sensor                  D2    trigger at sort point
Relay 1 / Fan 1            D4    active LOW
Relay 2 / Fan 2            D7    active LOW
Servo 4                    D8    open=0 closed=95
Servo 1                    D9    DISABLED / not used
Servo 2                    D10   open=0 closed=89
Servo 3                    D11   open=90 closed=0
```

## 3. Servo Rules

### Servo 1

Servo 1 is retired. The production firmware no longer attaches it.

- Dashboard no longer exposes gate buttons.
- Auto cycle no longer opens/closes a gate.
- If old code sends `SERVO1:OPEN` or `SERVO1:CLOSE`, Arduino replies:

```text
SERVO1:DISABLED
```

### Servo 2 + Servo 3 flap pair

These two are the real sorter now.

```text
Ripe    -> Servo 2 CLOSED + Servo 3 OPEN
Unripe  -> Servo 2 OPEN   + Servo 3 CLOSED
Rotten  -> Servo 2 OPEN   + Servo 3 OPEN
```

Mechanical safety rule:

```text
Servo 2 CLOSED + Servo 3 CLOSED is forbidden.
```

The firmware enforces that. It will not intentionally command both closed.

### Saved angles

From `config/servo_angles.json`:

```json
{
  "open": 50,
  "closed": 0,
  "servo2_open": 0,
  "servo2_closed": 89,
  "servo3_open": 90,
  "servo3_closed": 0,
  "servo4_open": 0,
  "servo4_closed": 95
}
```

Meaning:

```text
Servo 1 legacy open  = 50
Servo 1 legacy closed= 0
Servo 2 open         = 0
Servo 2 closed       = 89
Servo 3 open         = 90
Servo 3 closed       = 0
Servo 4 open         = 0
Servo 4 closed       = 95
```

## 4. Power and Wiring Notes

### Servos

Servos are powered from an external 5V supply, not from Arduino 5V.

```text
Servo red          -> external 5V +
Servo brown/black  -> external 5V -
Arduino GND        -> same external 5V -
Servo signal       -> Arduino signal pin
```

Shared ground is mandatory.

### Conveyor BTS7960 / BTS7960-style board

Logic side:

```text
BTS VCC   -> Pi 5V
BTS GND   -> Pi GND
BTS R_EN  -> Pi 5V rail
BTS L_EN  -> Pi 5V rail
BTS RPWM  -> Pi GPIO18 (physical pin 12)
BTS LPWM  -> Pi GPIO19 (physical pin 35)
BTS R_IS  -> leave disconnected
BTS L_IS  -> leave disconnected
```

Motor side:

```text
BTS B+    -> external DC supply +
BTS B-    -> external DC supply -
BTS M+    -> conveyor motor wire 1
BTS M-    -> conveyor motor wire 2
```

Do not feed AC directly into the BTS board. Use a DC supply only.

### Dual relay for fans

Arduino control side:

```text
Relay VCC -> Arduino 5V
Relay GND -> Arduino GND
Relay IN1 -> Arduino D4
Relay IN2 -> Arduino D7
```

Fan power side:

```text
12V+      -> COM1 and COM2
NO1       -> Fan 1 red
NO2       -> Fan 2 red
Fan black -> 12V-
NC pins   -> unused
```

If your relay board has `JD-VCC`, wire it according to the relay coil voltage printed on the relay can.

## 5. Active Firmware / Sketches

Arduino can run only one sketch at a time.

### Production firmware

Use for the real system and dashboard:

```text
arduino/sketches/tomato_sorter
```

### Calibration firmware

Use for Servo 2, Servo 3, and Servo 4 calibration:

```text
arduino/sketches/servo23_calibrate
```

Notes:

- despite the name, `servo23_calibrate` now covers Servo 2, Servo 3, and Servo 4
- it no longer attaches Servo 1

Servo 1 calibration files still exist in the repo, but Servo 1 is currently disabled and not part of the machine flow.

## 6. Python Tools

```text
scripts/servo2_only.py        Servo 2 calibration
scripts/servo3_only.py        Servo 3 calibration
scripts/servo4_only.py        Servo 4 calibration
scripts/servo23_calibrate.py  dual Servo 2+3 calibration/testing
scripts/ir_test.py            IR monitor
scripts/test_dht22.py         DHT22 test
scripts/test_camera.py        camera + detector test
```

## 7. Calibration Workflow

### Calibrate Servo 2 / 3 / 4

1. Upload the combined calibration sketch:

```bash
~/.local/bin/arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino/sketches/servo23_calibrate
```

2. Run one of these:

```bash
.venv/bin/python scripts/servo2_only.py
.venv/bin/python scripts/servo3_only.py
.venv/bin/python scripts/servo4_only.py
```

3. Move the servo by typing angles like:

```text
0
90
180
```

4. Save the positions:

```text
save
open
```

and later:

```text
save
closed
```

### Dual flap test

```bash
.venv/bin/python scripts/servo23_calibrate.py
```

Useful commands:

```text
test ripe
test unripe
test rotten
```

### Back to production

After calibration, re-upload the production firmware:

```bash
~/.local/bin/arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino/sketches/tomato_sorter
```

## 8. Dashboard Manual Controls

Current dashboard manual actions:

```text
Conveyor Fwd
Conveyor Rev
Conveyor Stop
Servo 4 Open
Servo 4 Close
Sort Ripe
Sort Unripe
Sort Rotten
Fan 1 On / Off
Fan 2 On / Off
```

There are no Servo 1 / gate buttons anymore.

## 9. API Endpoints

```text
GET   /                         dashboard
GET   /stream                   camera stream
GET   /api/state                full live state
GET   /api/detections           current detector output
GET   /api/arduino/inbox        recent Arduino messages
POST  /api/start                start auto cycle
POST  /api/stop                 stop auto cycle
POST  /api/reset                clear counts/history
POST  /api/manual/conveyor_forward
POST  /api/manual/conveyor_reverse
POST  /api/manual/conveyor_stop
POST  /api/manual/servo4_open
POST  /api/manual/servo4_close
POST  /api/manual/sort_ripe
POST  /api/manual/sort_unripe
POST  /api/manual/sort_rotten
POST  /api/manual/fan1_on
POST  /api/manual/fan1_off
POST  /api/manual/fan2_on
POST  /api/manual/fan2_off
```

Quick checks:

```bash
curl -s http://localhost:5000/api/state | python3 -m json.tool
curl -X POST http://localhost:5000/api/manual/sort_ripe
curl -X POST http://localhost:5000/api/manual/conveyor_forward
curl -X POST http://localhost:5000/api/manual/fan1_on
```

## 10. Pi <-> Arduino Serial Protocol

Production firmware accepts:

```text
SERVO1:OPEN      disabled; replies SERVO1:DISABLED
SERVO1:CLOSE     disabled; replies SERVO1:DISABLED
SERVO2:LEFT      ripe
SERVO2:CENTER    unripe
SERVO2:RIGHT     rotten/rest
SERVO4:OPEN
SERVO4:CLOSE
RELAY1:ON
RELAY1:OFF
RELAY2:ON
RELAY2:OFF
PING
STATUS
```

Common async messages back from Arduino:

```text
READY
IR:TRIGGERED
IR:CLEAR
SERVO2:DONE
SERVO3:DONE
SERVO4:DONE
SERVO1:DISABLED
```

## 11. Current Auto-Cycle Logic

Servo 1 is no longer part of the cycle.

The current cycle is:

```text
START
  -> flaps return to both-open rest
  -> camera keeps classifying tomatoes on the conveyor
  -> wait for IR trigger
  -> if IR never triggers, skip sort
  -> if IR triggers:
       wait ir_sort_delay_ms
       ripe    -> Servo 2 closed + Servo 3 open
       unripe  -> Servo 2 open   + Servo 3 closed
       rotten  -> Servo 2 open   + Servo 3 open
  -> hold sort position
  -> return to both-open rest
  -> repeat
```

This means tomatoes are expected to be fed into the conveyor without a gate servo.

Timing knob:

```yaml
cycle:
  min_travel_ms: 1500
  ir_sort_delay_ms: 0
  ir_sort_cooldown_ms: 2500
  require_detection: true
```

Use `min_travel_ms` to ignore early IR triggers. Use `ir_sort_cooldown_ms` to prevent repeat flap movement from one tomato/noisy IR signal. With `require_detection: true`, IR alone will not sort unless the camera has seen a tomato.

## 12. Troubleshooting

### `UNKNOWN: B:90` or `UNKNOWN: C:90` or `UNKNOWN: D:90`

Wrong sketch is loaded on Arduino.

For Servo 2/3/4 calibration, upload:

```bash
~/.local/bin/arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino/sketches/servo23_calibrate
```

For the real dashboard/system, upload:

```bash
~/.local/bin/arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino/sketches/tomato_sorter
```

### Servo responds in terminal but does not move

Usually wiring or power.

Checklist:

```text
1. external 5V supply present
2. servo ground tied to Arduino ground
3. signal wire on the correct Arduino pin
4. no loose jumper
5. servo is not jammed
```

### Conveyor buttons change state but motor does not spin

Check BTS motor-side power first:

```text
B+ / B- must be on the external DC motor supply
M+ / M- must go to the motor
R_EN and L_EN must be enabled
Pi GND and BTS GND must be common
```

### Relay clicks but fans do not spin

That means control logic is probably fine. Check:

```text
COM/NO wiring
fan polarity
12V fan supply
JD-VCC / relay coil wiring
```

### Need to verify the Arduino firmware quickly

Run:

```bash
.venv/bin/python - <<'PY'
import serial, time
a = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)
a.write(b'STATUS\n')
time.sleep(0.5)
while a.in_waiting:
    print(a.readline().decode(errors='ignore').strip())
a.close()
PY
```

Production firmware should mention `sorter`, `sorter3`, `servo4`, and relays.

## 13. Key Files

```text
config/settings.yaml
config/servo_angles.json
arduino/sketches/tomato_sorter/tomato_sorter.ino
arduino/sketches/servo23_calibrate/servo23_calibrate.ino
src/tomato_sorter/main.py
src/tomato_sorter/orchestrator.py
src/tomato_sorter/server.py
src/tomato_sorter/conveyor.py
src/tomato_sorter/templates/dashboard.html
```
