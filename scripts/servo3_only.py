#!/usr/bin/env python3
"""
Simple single-servo calibration for Servo 3 (pin 11).
Mirrors servo_calibrate.py exactly — proven reliable pattern.

Type a number 0-180 and press Enter, servo moves there.
Commands: sweep / pulse / save / status / quit
"""
import json, time
from pathlib import Path
import serial

PORT = "/dev/ttyUSB0"
BAUD = 9600
SAVE = Path("config/servo_angles.json")


def main():
    SAVE.parent.mkdir(exist_ok=True)
    saved = json.loads(SAVE.read_text()) if SAVE.exists() else {}
    missing = [name for name in ("servo2_open", "servo3_open") if name not in saved]
    if missing:
        raise SystemExit(f"Missing saved position(s): {', '.join(missing)}. Save the open positions first.")
    servo2_open = int(saved["servo2_open"])
    servo3_open = int(saved["servo3_open"])

    print(f"Connecting to Arduino on {PORT} without auto-reset...")
    ard = serial.Serial()
    ard.port = PORT
    ard.baudrate = BAUD
    ard.timeout = 1
    ard.dtr = False
    ard.open()
    time.sleep(0.2)
    ard.reset_input_buffer()
    ard.reset_output_buffer()

    print(f"Moving flaps to saved OPEN positions: Servo 2={servo2_open}, Servo 3={servo3_open}...")
    ard.write(f"B:{servo2_open}\n".encode()); ard.flush()
    time.sleep(0.15)
    ard.write(f"C:{servo3_open}\n".encode()); ard.flush()
    time.sleep(0.25)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line: print(f"  arduino: {line}")

    ard.write(b"STATUS\n"); ard.flush()
    time.sleep(0.5)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line: print(f"  arduino: {line}")

    print("\n=== SERVO 3 (PIN 11) — SIMPLE CALIBRATION ===")
    print("Type angle 0-180, or: sweep / pulse / save / status / quit\n")
    print("Saved so far:", saved or "{}")
    print()

    last_angle = None

    while True:
        try:
            cmd = input("angle> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd: continue
        if cmd in ("q", "quit", "exit"): break

        drain_seconds = 0.15

        if cmd == "status":
            ard.write(b"STATUS\n"); ard.flush()
        elif cmd == "sweep":
            ard.write(b"SWEEP3\n"); ard.flush()
            drain_seconds = 4.0
        elif cmd == "pulse":
            ard.write(b"PULSE3\n"); ard.flush()
            drain_seconds = 6.0
        elif cmd == "save":
            if last_angle is None:
                print("  -> move to an angle first"); continue
            label = input(f"  save {last_angle} as (open/closed): ").strip().lower()
            if label not in ("open", "closed"):
                print("  -> must be 'open' or 'closed'"); continue
            saved[f"servo3_{label}"] = last_angle
            SAVE.write_text(json.dumps(saved, indent=2))
            print(f"  -> saved servo3_{label} = {last_angle}")
            continue
        else:
            try:
                deg = int(cmd)
            except ValueError:
                print("  -> not a number"); continue
            if not 0 <= deg <= 180:
                print("  -> 0-180 only"); continue
            ard.write(f"C:{deg}\n".encode()); ard.flush()
            last_angle = deg

        deadline = time.time() + drain_seconds
        while time.time() < deadline:
            if ard.in_waiting:
                line = ard.readline().decode(errors="ignore").strip()
                if line: print(f"  arduino: {line}")
                deadline = time.time() + 0.05
            else:
                time.sleep(0.01)

    ard.close()
    print(f"\nFinal saved: {saved}")


if __name__ == "__main__":
    main()
