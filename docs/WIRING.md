# Tomato Sorter v2.0 — Complete Wiring Diagram & Bill of Materials

> Hardware reference for recreating the system from scratch.
> All pin assignments verified against the production firmware
> (`arduino/sketches/tomato_sorter`) and `config/settings.yaml`.

---

## 1. Bill of Materials (Components)

| # | Component | Spec / Model | Qty | Notes |
|---|-----------|--------------|-----|-------|
| 1 | Raspberry Pi 5 | Model B, 8GB RAM | 1 | Main controller — runs YOLO + dashboard |
| 2 | Arduino Uno | (or CH340 clone) | 1 | Handles servos, IR, relays |
| 3 | USB Camera | any UVC webcam, ≥640×480 | 1 | `/dev/video*`, V4L2 |
| 4 | 7-inch DSI Display | Official Pi touchscreen | 1 | Kiosk dashboard screen |
| 5 | DHT22 (AM2302) | temp/humidity sensor | 2 | One per bin (ripe + unripe) |
| 6 | Servo motor | SG90 / MG996R (standard PWM) | 3 | Servo 2, 3 (sorter flaps), Servo 4 |
| 7 | IR obstacle sensor | FC-51 / active-low module | 1 | Sort-point trigger |
| 8 | Dual relay module | 12V coil, active-LOW | 1 | Drives 2 fans |
| 9 | DC fans | 12V | 2 | Bin cooling (ripe + unripe) |
| 10 | DC motor | 12V geared | 1 | Conveyor belt |
| 11 | BTS7960 motor driver | 43A H-bridge | 1 | Conveyor speed/direction (PWM) |
| 12 | 5V PSU (external) | ≥3A | 1 | Powers all servos (NOT from Pi/Arduino) |
| 13 | 12V PSU | ≥5A | 1 | Powers conveyor + fans |
| 14 | Breadboard + jumpers | — | — | Power rails + signal distribution |

---

## 2. Power Architecture (READ FIRST)

**Three separate power domains. Grounds MUST be common.**

```
                    ┌─────────────────────────────────────────┐
   USB-C 5V/5A  ───>│ Raspberry Pi 5                          │
                    │   + 7" DSI display (powered by Pi)      │
                    └─────────────────────────────────────────┘
                                  │ USB cable
                                  ▼
   USB (from Pi) ──>┌─────────────────────────────────────────┐
                    │ Arduino Uno (logic power from Pi USB)   │
                    └─────────────────────────────────────────┘

   External 5V PSU ──> Servo 2, Servo 3, Servo 4  (V+ and V−)
                       (Arduino sends ONLY signal wires)

   12V PSU ─────────> BTS7960 (conveyor motor)
            └───────> Relay load side → Fans
```

### ⚠️ The #1 mistake: missing common ground

ALL grounds must tie together:

```
Pi GND  ──┬── Arduino GND
          ├── External 5V PSU (−)
          ├── 12V PSU (−)
          └── BTS7960 GND
```

Without a shared ground, servos won't respond to signal pulses even
though they're powered, and the BTS7960 won't read PWM correctly.

---

## 3. Raspberry Pi 5 — GPIO Connections

Pi uses the RP1 chip — use `gpiozero` + `lgpio` in software (NOT `RPi.GPIO`).

| Pi Function | BCM GPIO | Physical Pin | Connects To |
|-------------|----------|--------------|-------------|
| DHT22 #1 (Ripe bin) data | GPIO 4 | Pin 7 | DHT22 #1 DATA |
| DHT22 #2 (Unripe bin) data | GPIO 23 | Pin 16 | DHT22 #2 DATA |
| Conveyor RPWM | GPIO 18 | Pin 12 | BTS7960 RPWM |
| Conveyor LPWM | GPIO 19 | Pin 35 | BTS7960 LPWM |
| 3.3V power | — | Pin 1 / 17 | DHT22 VCC (both) |
| 5V power | — | Pin 2 / 4 | BTS7960 VCC, R_EN, L_EN |
| Ground | — | Pin 6/9/14/20/25/30/34/39 | Common GND rail |
| Arduino link | — | USB port | Arduino Uno (`/dev/ttyUSB0`) |
| Camera | — | USB port | USB webcam (`/dev/video*`) |
| Display | — | DSI connector | 7" DSI screen |

### DHT22 wiring (×2, identical except data pin)

```
DHT22          Raspberry Pi
─────          ────────────
VCC (+)   ───> 3.3V  (pin 1 or 17)
DATA      ───> GPIO 4  (ripe)  / GPIO 23 (unripe)
GND (−)   ───> GND
```
> Add a 10kΩ pull-up resistor between VCC and DATA if your DHT22
> module is a bare sensor (most breakout boards have it built in).
> DHT22 read failure rate is 40–60% — the software caches last good value.

---

## 4. Arduino Uno — Connections

The Arduino handles all real-time motion + sensing. Pi talks to it over
USB serial (9600 baud).

| Arduino Pin | Function | Connects To | Notes |
|-------------|----------|-------------|-------|
| D2 | IR sensor input | IR module OUT | active LOW (LOW = object detected) |
| D4 | Relay 1 control | Relay IN1 | active LOW → Fan 1 |
| D7 | Relay 2 control | Relay IN2 | active LOW → Fan 2 |
| D8 | Servo 4 signal | Servo 4 signal wire | open=75°, closed=0° |
| D9 | Servo 1 (DISABLED) | — | retired, not connected |
| D10 | Servo 2 signal | Servo 2 signal wire | open=0°, closed=89° |
| D11 | Servo 3 signal | Servo 3 signal wire | open=90°, closed=0° |
| 5V | Logic 5V | Relay VCC | relay logic side only |
| GND | Ground | Common GND rail | MANDATORY shared ground |

---

## 5. Subsystem Wiring Detail

### 5.1 Servos (×3) — powered by EXTERNAL 5V PSU

```
                External 5V PSU
                  +        −
                  │        │
       ┌──────────┼────────┼──────────┐
       │          │        │          │  (breadboard rails)
   Servo 2    Servo 3   Servo 4
   ───────    ───────   ───────
   Red   ─────> 5V+ rail
   Brown ─────> 5V− rail (GND)
   Signal────> Arduino D10 / D11 / D8

   IMPORTANT: External 5V (−) rail also wires to Arduino GND.
```

Servo angle calibration (baked into firmware):

| Servo | Role | OPEN | CLOSED |
|-------|------|------|--------|
| Servo 2 | Sorter flap A | 0° | 89° |
| Servo 3 | Sorter flap B | 90° | 0° |
| Servo 4 | Feeder/agitator | 75° | 0° |

> Mechanical rule: Servo 2 and Servo 3 must **never both be closed**
> (they collide). Firmware enforces this.

### 5.2 IR Sensor — Arduino D2

```
IR Module        Arduino
─────────        ───────
VCC      ──────> 5V
GND      ──────> GND
OUT      ──────> D2

LOW  on OUT = object detected  → firmware emits IR:TRIGGERED
HIGH on OUT = clear            → firmware emits IR:CLEAR
```
> Most FC-51 modules have a sensitivity potentiometer — adjust it so
> the DETECT LED lights when a tomato is at the sort point.

### 5.3 Dual Relay + Fans — 12V coil, active LOW

```
Logic side (Arduino):
  Relay VCC ───> Arduino 5V
  Relay GND ───> Arduino GND
  Relay IN1 ───> Arduino D4   (Fan 1)
  Relay IN2 ───> Arduino D7   (Fan 2)
  (If module has JD-VCC jumper: wire JD-VCC to 12V if coils are 12V)

Load side (12V fans):
  12V (+) ───> COM1 and COM2
  NO1     ───> Fan 1 (+)
  NO2     ───> Fan 2 (+)
  Fan (−) ───> 12V (−)
  NC pins ───> unused
```
> Active LOW: Arduino pin LOW = relay ON = fan spins.
> Fans default ON at Arduino boot.

### 5.4 Conveyor — BTS7960 driver, 12V motor, PWM speed control

```
Logic side (Raspberry Pi):
  BTS VCC  ───> Pi 5V
  BTS GND  ───> Pi GND (common rail)
  BTS R_EN ───> Pi 5V   (enable)
  BTS L_EN ───> Pi 5V   (enable)
  BTS RPWM ───> Pi GPIO 18 (pin 12)   forward PWM
  BTS LPWM ───> Pi GPIO 19 (pin 35)   reverse PWM
  BTS R_IS ───> leave disconnected
  BTS L_IS ───> leave disconnected

Motor side (12V):
  BTS B+ ───> 12V PSU (+)
  BTS B− ───> 12V PSU (−)
  BTS M+ ───> conveyor motor wire 1
  BTS M− ───> conveyor motor wire 2
```
> Speed is controlled by software PWM (0–100%) at 1 kHz from the dashboard
> slider. Forward = RPWM duty cycle, Reverse = LPWM duty cycle.
> Feed only a DC supply to B+/B− — never AC.

---

## 6. Full System Block Diagram

```
                            ┌────────────────────┐
                            │   12V PSU (≥5A)     │
                            └──┬──────────────┬───┘
                               │              │
                    ┌──────────▼───┐   ┌──────▼──────┐
                    │  BTS7960     │   │ Relay (×2)  │
                    │  (conveyor)  │   │  load side  │
                    └──┬───────┬───┘   └──┬───────┬──┘
            GPIO18/19  │       │ motor    │       │
        ┌──────────────┘     ┌─▼──┐    ┌──▼─┐  ┌──▼─┐
        │   (PWM)            │Belt│    │Fan1│  │Fan2│
        │                   └────┘    └────┘  └────┘
   ┌────▼─────────┐                      ▲       ▲
   │ Raspberry Pi │                      │D4     │D7
   │     5        │       ┌──────────────┴───────┴──────┐
   │              │  USB  │       Arduino Uno            │
   │  - YOLO      ├──────>│  D2 ◄── IR sensor            │
   │  - Dashboard │       │  D8 ──► Servo 4              │
   │  - Conveyor  │       │  D10──► Servo 2  ┐ sorter    │
   │    PWM       │       │  D11──► Servo 3  ┘ flaps     │
   │  GPIO4 ◄─DHT22(ripe) │                              │
   │  GPIO23◄─DHT22(unrip) └──────────────┬──────────────┘
   │              │                       │ signal only
   │  + 7" DSI    │                ┌──────▼──────┐
   │    display   │                │ External 5V │
   │  + USB cam   │                │   PSU       │──► Servo 2,3,4 power
   └──────────────┘                └─────────────┘

   ══════════ COMMON GROUND (all PSU −, Pi GND, Arduino GND) ══════════
```

---

## 7. Bins / Sorting Logic

| Bin | Class | DHT22 | Fan | Sorter combo |
|-----|-------|-------|-----|--------------|
| Bin 1 | Ripe | Yes (GPIO 4) | Yes (Relay 1) | Servo 2 CLOSED + Servo 3 OPEN |
| Bin 2 | Unripe | Yes (GPIO 23) | Yes (Relay 2) | Servo 2 OPEN + Servo 3 CLOSED |
| Bin 3 | Rotten | No | No | Servo 2 OPEN + Servo 3 OPEN (passthrough) |

Sorting flow: Camera classifies (YOLO) → tomato travels on conveyor →
IR sensor triggers at sort point → Servo 2/3 flap moves to route the
tomato into the correct bin → returns to rest.

---

## 8. Quick Pin Reference (cheat card)

```
RASPBERRY PI 5            ARDUINO UNO
─────────────            ───────────
GPIO4  (pin7)  DHT22 ripe    D2   IR sensor OUT
GPIO23 (pin16) DHT22 unripe  D4   Relay 1 (Fan 1)
GPIO18 (pin12) BTS RPWM      D7   Relay 2 (Fan 2)
GPIO19 (pin35) BTS LPWM      D8   Servo 4
3.3V   (pin1)  DHT22 VCC     D10  Servo 2
5V     (pin2)  BTS logic     D11  Servo 3
USB            Arduino+Cam   (D9  Servo 1 = DISABLED)

POWER: Pi=USB-C 5V | Servos=ext 5V PSU | Conveyor+Fans=12V PSU
GROUND: all commoned together
```
