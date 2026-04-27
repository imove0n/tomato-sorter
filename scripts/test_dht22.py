#!/usr/bin/env python3
"""
DHT22 dual sensor test.

Reads both DHT22s and prints temperature + humidity every 2 seconds.
DHT22 typically fails 40-60% of reads — that's normal, just retry.

Wiring:
    DHT22 #1 (Ripe bin)    -> GPIO 4   (physical pin 7)
    DHT22 #2 (Unripe bin)  -> GPIO 23  (physical pin 16)
    Both VCC -> Pi 3.3V, GND -> Pi GND
"""
import time
import board
import adafruit_dht

PIN_RIPE   = board.D4
PIN_UNRIPE = board.D23

def main():
    print("Initializing DHT22 sensors...")
    dht_ripe   = adafruit_dht.DHT22(PIN_RIPE,   use_pulseio=False)
    dht_unripe = adafruit_dht.DHT22(PIN_UNRIPE, use_pulseio=False)
    print("Sensors initialized. Reading every 2s. Ctrl+C to stop.\n")

    success = {"ripe": 0, "unripe": 0}
    fail    = {"ripe": 0, "unripe": 0}

    try:
        while True:
            ts = time.strftime("%H:%M:%S")

            # Sensor 1 (Ripe bin)
            try:
                t1 = dht_ripe.temperature
                h1 = dht_ripe.humidity
                if t1 is not None and h1 is not None:
                    success["ripe"] += 1
                    print(f"  [{ts}] RIPE   bin: {t1:5.1f}C  {h1:5.1f}%RH  "
                          f"(ok:{success['ripe']} fail:{fail['ripe']})")
                else:
                    fail["ripe"] += 1
                    print(f"  [{ts}] RIPE   bin: read returned None  "
                          f"(ok:{success['ripe']} fail:{fail['ripe']})")
            except RuntimeError as e:
                fail["ripe"] += 1
                print(f"  [{ts}] RIPE   bin: read failed ({e})  "
                      f"(ok:{success['ripe']} fail:{fail['ripe']})")

            time.sleep(0.5)

            # Sensor 2 (Unripe bin)
            try:
                t2 = dht_unripe.temperature
                h2 = dht_unripe.humidity
                if t2 is not None and h2 is not None:
                    success["unripe"] += 1
                    print(f"  [{ts}] UNRIPE bin: {t2:5.1f}C  {h2:5.1f}%RH  "
                          f"(ok:{success['unripe']} fail:{fail['unripe']})")
                else:
                    fail["unripe"] += 1
                    print(f"  [{ts}] UNRIPE bin: read returned None  "
                          f"(ok:{success['unripe']} fail:{fail['unripe']})")
            except RuntimeError as e:
                fail["unripe"] += 1
                print(f"  [{ts}] UNRIPE bin: read failed ({e})  "
                      f"(ok:{success['unripe']} fail:{fail['unripe']})")

            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n\nFinal stats:")
        for sensor in ("ripe", "unripe"):
            total = success[sensor] + fail[sensor]
            rate = (success[sensor] / total * 100) if total else 0
            print(f"  {sensor.upper():6s}: {success[sensor]}/{total} "
                  f"successful ({rate:.0f}%)")
    finally:
        dht_ripe.exit()
        dht_unripe.exit()

if __name__ == "__main__":
    main()
