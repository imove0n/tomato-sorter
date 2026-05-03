#!/usr/bin/env python3
"""
Simple single-servo calibration for Servo 2 (pin 10).
Mirrors servo_calibrate.py exactly — proven reliable pattern.

Type a number 0-180 and press Enter, servo moves there.
Commands: save / status / quit
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

    print(f"Connecting to Arduino on {PORT}...")
    ard = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    ard.reset_input_buffer()
    ard.reset_output_buffer()

    ard.write(b"STATUS\n"); ard.flush()
    time.sleep(0.5)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line: print(f"  arduino: {line}")

    print("\n=== SERVO 2 (PIN 10) — SIMPLE CALIBRATION ===")
    print("Type angle 0-180, or: save / status / quit\n")
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

        if cmd == "status":
            ard.write(b"STATUS\n"); ard.flush()
        elif cmd == "save":
            if last_angle is None:
                print("  -> move to an angle first"); continue
            label = input(f"  save {last_angle} as (open/closed): ").strip().lower()
            if label not in ("open", "closed"):
                print("  -> must be 'open' or 'closed'"); continue
            saved[f"servo2_{label}"] = last_angle
            SAVE.write_text(json.dumps(saved, indent=2))
            print(f"  -> saved servo2_{label} = {last_angle}")
            continue
        else:
            try:
                deg = int(cmd)
            except ValueError:
                print("  -> not a number"); continue
            if not 0 <= deg <= 180:
                print("  -> 0-180 only"); continue
            ard.write(f"B:{deg}\n".encode()); ard.flush()
            last_angle = deg

        # drain — exact same pattern as servo_calibrate.py
        deadline = time.time() + 0.15
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
