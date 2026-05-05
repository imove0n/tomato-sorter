#!/bin/bash
# Tomato Sorter — safely flash the production firmware while the
# systemd service is running. Stops the service, flashes, restarts.
#
# Usage:  bash deploy/flash-production.sh
# Will prompt once for sudo password.

set -e

SKETCH="/home/bacadasa/tomato-sorter/arduino/sketches/tomato_sorter"
PORT="/dev/ttyUSB0"
FQBN="arduino:avr:uno"

echo "==> Stopping tomato-sorter service to free $PORT…"
sudo systemctl stop tomato-sorter
sleep 1

echo "==> Compiling production sketch…"
arduino-cli compile --fqbn "$FQBN" "$SKETCH"

echo "==> Uploading to Arduino…"
arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$SKETCH"

echo "==> Restarting tomato-sorter service…"
sudo systemctl start tomato-sorter

echo "==> Waiting for backend to come up…"
for i in $(seq 1 15); do
    if curl -sf http://localhost:5000/api/state >/dev/null 2>&1; then
        echo "    backend ready after ${i}s"
        break
    fi
    sleep 1
done

echo
echo "==> Verifying Arduino is on production firmware…"
sleep 3
INBOX=$(curl -s http://localhost:5000/api/arduino/inbox)
if echo "$INBOX" | grep -q '"UNKNOWN:'; then
    echo "    !!! still seeing UNKNOWN messages — flash may have failed"
    echo "$INBOX" | python3 -m json.tool | tail -20
    exit 1
else
    echo "    no UNKNOWN messages — production firmware accepted commands ✓"
fi

echo
echo "Done. Press START CYCLE on the dashboard to test Servo 4 oscillation."
