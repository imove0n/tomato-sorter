#!/usr/bin/env python3
"""
Live IR sensor monitor.
Wave your hand or pass an object in front of the sensor — you'll see TRIGGER events.
Press Ctrl+C to stop.
"""
import time
import serial

PORT = "/dev/ttyUSB0"
BAUD = 9600

def main():
    print(f"Connecting to Arduino on {PORT}...")
    ard = serial.Serial(PORT, BAUD, timeout=0.5)
    time.sleep(2)

    # Drain boot banner
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line:
            print(f"  arduino: {line}")

    # Ask for current state
    ard.write(b"STATUS\n"); ard.flush()
    time.sleep(0.2)
    while ard.in_waiting:
        line = ard.readline().decode(errors="ignore").strip()
        if line:
            print(f"  arduino: {line}")

    print("\n=== LIVE IR MONITOR ===")
    print("Wave hand / pass tomato in front of sensor. Ctrl+C to stop.\n")

    trigger_count = 0
    try:
        while True:
            line = ard.readline().decode(errors="ignore").strip()
            if not line:
                continue
            ts = time.strftime("%H:%M:%S")
            if line == "IR:TRIGGERED":
                trigger_count += 1
                print(f"  [{ts}] >>> TRIGGERED <<<   (total triggers: {trigger_count})")
            elif line == "IR:CLEAR":
                print(f"  [{ts}]     cleared")
            else:
                print(f"  [{ts}] {line}")
    except KeyboardInterrupt:
        print(f"\nStopped. Total triggers detected: {trigger_count}")
    finally:
        ard.close()

if __name__ == "__main__":
    main()
