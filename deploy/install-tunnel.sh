#!/bin/bash
# Tomato Sorter — install the Cloudflare quick-tunnel as a systemd service.
#
# After this runs, the Pi will always have a public *.trycloudflare.com URL
# pointing to its dashboard (auto-restarts on crash / boots at startup).
#
# Usage:  bash deploy/install-tunnel.sh

set -e

PROJECT_DIR="/home/bacadasa/tomato-sorter"
SRC="$PROJECT_DIR/deploy/tomato-tunnel.service"
DST="/etc/systemd/system/tomato-tunnel.service"
RUNNER="$PROJECT_DIR/deploy/tunnel-runner.sh"

chmod +x "$RUNNER"

if [ ! -x "$PROJECT_DIR/bin/cloudflared" ]; then
    echo "!! cloudflared binary missing — re-run the download step:"
    echo "   curl -sL -o $PROJECT_DIR/bin/cloudflared \\"
    echo "        https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    echo "   chmod +x $PROJECT_DIR/bin/cloudflared"
    exit 1
fi

echo "==> Installing systemd service…"
sudo cp "$SRC" "$DST"
sudo systemctl daemon-reload
sudo systemctl enable tomato-tunnel.service
sudo systemctl restart tomato-tunnel.service

echo "==> Waiting for tunnel URL to come up (up to 30s)…"
URL=""
for i in $(seq 1 30); do
    URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' \
          "$PROJECT_DIR/data/logs/tunnel.log" 2>/dev/null | head -1 || true)
    if [ -n "$URL" ]; then
        echo "    Tunnel URL: $URL"
        break
    fi
    sleep 1
done

if [ -z "$URL" ]; then
    echo "    !! tunnel did not produce a URL within 30s. Check:"
    echo "       journalctl -u tomato-tunnel -n 50 --no-pager"
    exit 1
fi

echo
echo "==> Done. Status:"
sudo systemctl --no-pager --lines=3 status tomato-tunnel.service || true
echo
echo "Open the dashboard's 📱 Phone Access modal — the QR code is shown there."
echo "The URL above changes on every tunnel restart (use a permanent named tunnel for a stable URL)."
