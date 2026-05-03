#!/usr/bin/env python3
"""
Interactive Servo 2 + Servo 3 dual calibration tool.

Calibrate both flap servos as a pair. Each one needs an OPEN and a CLOSED angle.

Commands at the prompt:
    s2 <deg>    move Servo 2 to that angle
    s3 <deg>    move Servo 3 to that angle
    save s2 open|closed     save current Servo 2 angle as that label
    save s3 open|closed     save current Servo 3 angle as that label
    test ripe   test the Ripe combo (Servo 2 closed + Servo 3 open)
    test unripe test the Unripe combo (Servo 2 open + Servo 3 closed)
    test rotten test the Rotten combo (Servo 2 open + Servo 3 open)
    status      show current state
    quit        exit
"""
import json
import time
from pathlib import Path

import serial

PORT = "/dev/ttyUSB0"
BAUD = 9600
SAVE = Path("config/servo_angles.json")


def main():
    SAVE.parent.mkdir(exist_ok=True)
    saved = json.loads(SAVE.read_text()) if SAVE.exists() else {}
    last_s2 = None
    last_s3 = None

    print(f"Connecting to Arduino on {PORT}...")
    ard = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)

    # Hard-flush any stale data from previous sessions
    ard.reset_input_buffer()
    ard.reset_output_buffer()

    # Verify Arduino is alive
    ard.write(b"STATUS\n"); ard.flush()
    time.sleep(0.5)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line:
            print(f"  arduino: {line}")

    print("\n=== SERVO 2 + 3 DUAL CALIBRATION ===")
    print("Goal: dial in OPEN and CLOSED angles for each servo.\n")
    print("Commands:")
    print("  s2 <0-180>          move Servo 2")
    print("  s3 <0-180>          move Servo 3")
    print("  save s2 open|closed save current Servo 2 angle")
    print("  save s3 open|closed save current Servo 3 angle")
    print("  test ripe|unripe|rotten   test combinations")
    print("  status              show angles")
    print("  quit\n")
    print("Currently saved:", saved or "{}")
    print()

    def send(cmd: str):
        ard.write((cmd + "\n").encode())
        ard.flush()
        deadline = time.time() + 0.2
        while time.time() < deadline:
            if ard.in_waiting:
                line = ard.readline().decode(errors="ignore").strip()
                if line:
                    print(f"  arduino: {line}")
                deadline = time.time() + 0.05
            else:
                time.sleep(0.01)

    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        if raw in ("q", "quit", "exit"):
            break

        parts = raw.split()
        cmd = parts[0]

        if cmd == "s2" and len(parts) == 2:
            try:
                deg = int(parts[1])
                if 0 <= deg <= 180:
                    send(f"B:{deg}")
                    last_s2 = deg
                else:
                    print("  -> 0-180 only")
            except ValueError:
                print("  -> not a number")

        elif cmd == "s3" and len(parts) == 2:
            try:
                deg = int(parts[1])
                if 0 <= deg <= 180:
                    send(f"C:{deg}")
                    last_s3 = deg
                else:
                    print("  -> 0-180 only")
            except ValueError:
                print("  -> not a number")

        elif cmd == "save" and len(parts) == 3:
            target, label = parts[1], parts[2]
            if target == "s2" and label in ("open", "closed"):
                if last_s2 is None:
                    print("  -> move Servo 2 first")
                    continue
                saved[f"servo2_{label}"] = last_s2
                SAVE.write_text(json.dumps(saved, indent=2))
                print(f"  -> saved servo2_{label} = {last_s2}")
            elif target == "s3" and label in ("open", "closed"):
                if last_s3 is None:
                    print("  -> move Servo 3 first")
                    continue
                saved[f"servo3_{label}"] = last_s3
                SAVE.write_text(json.dumps(saved, indent=2))
                print(f"  -> saved servo3_{label} = {last_s3}")
            else:
                print("  -> save s2|s3 open|closed")

        elif cmd == "test" and len(parts) == 2:
            kind = parts[1]
            need = ["servo2_open", "servo2_closed", "servo3_open", "servo3_closed"]
            missing = [k for k in need if k not in saved]
            if missing:
                print(f"  -> missing: {missing}")
                continue
            if kind == "ripe":
                print("  -> RIPE: Servo 2 CLOSED + Servo 3 OPEN")
                send(f"B:{saved['servo2_closed']}")
                send(f"C:{saved['servo3_open']}")
            elif kind == "unripe":
                print("  -> UNRIPE: Servo 2 OPEN + Servo 3 CLOSED")
                send(f"B:{saved['servo2_open']}")
                send(f"C:{saved['servo3_closed']}")
            elif kind == "rotten":
                print("  -> ROTTEN: Servo 2 OPEN + Servo 3 OPEN")
                send(f"B:{saved['servo2_open']}")
                send(f"C:{saved['servo3_open']}")
            else:
                print("  -> test ripe|unripe|rotten")

        elif cmd == "status":
            send("STATUS")

        else:
            print("  -> unknown. Try: s2 <deg>, s3 <deg>, save s2/s3 open/closed, test ripe/unripe/rotten")

    ard.close()
    print(f"\nFinal saved: {saved}")
    print(f"File: {SAVE.resolve()}")


if __name__ == "__main__":
    main()
