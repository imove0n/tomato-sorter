#!/usr/bin/env python3
"""
Interactive servo calibration tool.

Usage:
    .venv/bin/python scripts/servo_calibrate.py

Type a number 0-180 and press Enter — servo moves there.
Special commands:
    sweep   - slow sweep 0->180->0
    status  - report last angle
    save    - save current angle as 'open' or 'closed' (you'll be asked which)
    quit    - exit
"""
import json
import sys
import time
from pathlib import Path

import serial

PORT  = "/dev/ttyUSB0"
BAUD  = 9600
SAVE  = Path("config/servo_angles.json")

def main():
    SAVE.parent.mkdir(exist_ok=True)
    saved = json.loads(SAVE.read_text()) if SAVE.exists() else {}

    print(f"Connecting to Arduino on {PORT}...")
    ard = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)

    # Hard-flush any stale data from previous sessions
    ard.reset_input_buffer()
    ard.reset_output_buffer()

    # Verify Arduino is alive and synced
    ard.write(b"STATUS\n"); ard.flush()
    time.sleep(0.5)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line:
            print(f"  arduino: {line}")

    print("\n=== SERVO 1 (GATE) CALIBRATION ===")
    print("Type angle (0-180), or: sweep / status / save / quit")
    print("Saved so far:", saved or "{}")
    print()

    last_angle = None

    while True:
        try:
            cmd = input("angle> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        if cmd in ("q", "quit", "exit"):
            break

        if cmd == "sweep":
            ard.write(b"SWEEP\n"); ard.flush()
        elif cmd == "status":
            ard.write(b"STATUS\n"); ard.flush()
        elif cmd == "save":
            if last_angle is None:
                print("  -> move to an angle first")
                continue
            label = input(f"  save {last_angle} deg as which label? (open/closed): ").strip().lower()
            if label not in ("open", "closed"):
                print("  -> must be 'open' or 'closed'")
                continue
            saved[label] = last_angle
            SAVE.write_text(json.dumps(saved, indent=2))
            print(f"  -> saved: {label} = {last_angle} (file: {SAVE})")
            continue
        else:
            try:
                deg = int(cmd)
            except ValueError:
                print("  -> not a number")
                continue
            if not 0 <= deg <= 180:
                print("  -> must be 0-180")
                continue
            ard.write(f"A:{deg}\n".encode()); ard.flush()
            last_angle = deg

        # Quick non-blocking drain (no fixed sleep)
        deadline = time.time() + 0.15
        while time.time() < deadline:
            if ard.in_waiting:
                line = ard.readline().decode(errors="ignore").strip()
                if line:
                    print(f"  arduino: {line}")
                deadline = time.time() + 0.05
            else:
                time.sleep(0.01)

    ard.close()
    print(f"\nFinal saved angles: {saved}")
    print(f"File: {SAVE.resolve()}")

if __name__ == "__main__":
    main()
