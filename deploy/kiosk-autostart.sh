#!/bin/bash
# Tomato Sorter — Chromium kiosk autostart
# Called by ~/.config/labwc/autostart on every desktop login.
# Waits for the backend systemd service to be reachable, then launches
# Chromium in fullscreen kiosk mode pointing at the dashboard.

set -u

DASHBOARD_URL="http://localhost:5000"
LOG="/home/bacadasa/tomato-sorter/data/logs/kiosk.log"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "[$(date '+%F %T')] kiosk-autostart starting"

# Wait up to 60s for backend to come up before opening the browser
for i in $(seq 1 60); do
    if curl -sf "$DASHBOARD_URL/api/state" >/dev/null 2>&1; then
        echo "[$(date '+%F %T')] backend ready after ${i}s"
        break
    fi
    sleep 1
done

# Hide cursor + power-saving off (keep DSI screen alive during demos)
if command -v xset >/dev/null 2>&1; then
    xset s off || true
    xset s noblank || true
    xset -dpms || true
fi

# Launch Chromium in kiosk mode. --noerrdialogs/--disable-* keep it clean
# for thesis defense — no popups, no prompts.
exec /usr/bin/chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --disable-features=TranslateUI \
    --no-first-run \
    --start-maximized \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    "$DASHBOARD_URL"
