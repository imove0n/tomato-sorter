#!/bin/bash
# Tomato Sorter — one-shot autostart installer.
# Run with: bash deploy/install-autostart.sh   (will prompt for sudo)
#
# Installs:
#   1. systemd service /etc/systemd/system/tomato-sorter.service
#      → backend auto-starts at boot, auto-restarts on crash
#   2. Confirms ~/.config/labwc/autostart points to kiosk-autostart.sh
#      → Chromium kiosk launches once desktop logs in
#
# After this runs, just reboot. Power on → 30s → dashboard live.

set -e

PROJECT_DIR="/home/bacadasa/tomato-sorter"
SERVICE_SRC="$PROJECT_DIR/deploy/tomato-sorter.service"
SERVICE_DST="/etc/systemd/system/tomato-sorter.service"
LABWC_AUTOSTART="/home/bacadasa/.config/labwc/autostart"
KIOSK_SCRIPT="$PROJECT_DIR/deploy/kiosk-autostart.sh"

echo "==> Installing systemd service…"
sudo cp "$SERVICE_SRC" "$SERVICE_DST"
sudo systemctl daemon-reload
sudo systemctl enable tomato-sorter.service
sudo systemctl restart tomato-sorter.service

echo "==> Installing sudoers rule for dashboard Shutdown/Reboot buttons…"
sudo cp "$PROJECT_DIR/deploy/tomato-sorter-sudoers" /etc/sudoers.d/tomato-sorter
sudo chmod 0440 /etc/sudoers.d/tomato-sorter
sudo visudo -c -f /etc/sudoers.d/tomato-sorter

echo "==> Verifying labwc kiosk autostart…"
mkdir -p "$(dirname "$LABWC_AUTOSTART")"
if ! grep -q "kiosk-autostart.sh" "$LABWC_AUTOSTART" 2>/dev/null; then
    echo "$KIOSK_SCRIPT &" >> "$LABWC_AUTOSTART"
    echo "    appended kiosk launcher to $LABWC_AUTOSTART"
else
    echo "    already present"
fi
chmod +x "$LABWC_AUTOSTART" "$KIOSK_SCRIPT"

echo
echo "==> Done."
echo
echo "Status check:"
sudo systemctl --no-pager --lines=5 status tomato-sorter.service || true
echo
echo "Reboot to verify the full kiosk flow:  sudo reboot"
