#!/usr/bin/env python3
"""
Calibration tool for 360° continuous rotation servos.

For each servo we need:
    1) NEUTRAL value (the exact PWM where it stops — usually 88-92)
    2) Duration in ms to rotate to OPEN
    3) Duration in ms to rotate back to CLOSED

Commands at the > prompt:
    probe 2          run probe (tries 85..95 for 2s each — pick the value where it didn't move)
    probe 3
    neutral 2 <val>  set Servo 2 neutral
    neutral 3 <val>  set Servo 3 neutral
    fwd 2 <ms>       Servo 2 spin forward for ms then stop
    rev 2 <ms>       Servo 2 spin reverse for ms then stop
    fwd 3 <ms>
    rev 3 <ms>
    stop 2           stop Servo 2 immediately
    stop 3
    save 2 open <ms>     save the open duration for Servo 2
    save 2 close <ms>    save the close duration for Servo 2
    save 2 neutral <val> save the neutral value
    save 3 ...           same for Servo 3
    status
    quit

Saved JSON keys:
    servo2_neutral, servo2_open_ms, servo2_close_ms
    servo3_neutral, servo3_open_ms, servo3_close_ms
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

    ard.write(b"STATUS\n"); ard.flush(); time.sleep(0.5)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line: print(f"  arduino: {line}")

    print("\n=== 360° SERVO CALIBRATION ===")
    print("Step-by-step process per servo:\n")
    print("  1.  probe N             — find true neutral (look for the value where servo stays still)")
    print("  2.  neutral N <val>     — set that value as the neutral")
    print("  3.  fwd N 200           — try 200ms forward, observe how far flap rotates")
    print("  4.  fwd N 300, 400...   — adjust until flap reaches OPEN position")
    print("  5.  save N open <ms>    — save the open duration")
    print("  6.  rev N <ms>          — same process for CLOSE direction")
    print("  7.  save N close <ms>")
    print("  8.  save N neutral <val>\n")
    print("Saved so far:", saved or "{}")
    print()

    def send(cmd, wait_extra=0):
        ard.write((cmd + "\n").encode())
        ard.flush()
        deadline = time.time() + 0.3 + wait_extra
        while time.time() < deadline:
            if ard.in_waiting:
                line = ard.readline().decode(errors="ignore").strip()
                if line:
                    print(f"  arduino: {line}")
                deadline = time.time() + 0.1
            else:
                time.sleep(0.02)

    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw: continue
        if raw in ("q", "quit", "exit"): break

        parts = raw.split()
        cmd = parts[0]

        if cmd == "probe" and len(parts) == 2 and parts[1] in ("2", "3"):
            send(f"PROBE{parts[1]}", wait_extra=24)   # probe takes 22s
        elif cmd == "neutral" and len(parts) == 3:
            n = parts[1]
            try: val = int(parts[2])
            except: print("  -> not a number"); continue
            send(f"N{n}:{val}")
        elif cmd in ("fwd", "rev") and len(parts) == 3:
            n = parts[1]
            try: ms = int(parts[2])
            except: print("  -> not a number"); continue
            letter = "F" if cmd == "fwd" else "R"
            send(f"{letter}{n}:{ms}", wait_extra=ms/1000.0 + 0.5)
        elif cmd == "stop" and len(parts) == 2:
            send(f"S{parts[1]}")
        elif cmd == "save" and len(parts) >= 3:
            n = parts[1]; what = parts[2]
            if what in ("open", "close", "neutral") and len(parts) == 4:
                try: val = int(parts[3])
                except: print("  -> bad number"); continue
                key_map = {"open": f"servo{n}_open_ms", "close": f"servo{n}_close_ms", "neutral": f"servo{n}_neutral"}
                saved[key_map[what]] = val
                SAVE.write_text(json.dumps(saved, indent=2))
                print(f"  -> saved {key_map[what]} = {val}")
            else:
                print("  -> save N open|close|neutral <value>")
        elif cmd == "status":
            send("STATUS")
        else:
            print("  -> usage: probe N | neutral N val | fwd N ms | rev N ms | stop N | save N open|close|neutral val | status | quit")

    ard.close()
    print(f"\nFinal saved: {saved}")
    print(f"File: {SAVE.resolve()}")


if __name__ == "__main__":
    main()
