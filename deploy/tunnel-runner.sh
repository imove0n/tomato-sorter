#!/bin/bash
# Tomato Sorter — Cloudflare quick-tunnel runner.
#
# Runs cloudflared in --url mode, which produces a random
# *.trycloudflare.com public URL for the dashboard. No Cloudflare
# account or domain required.
#
# Output goes to data/logs/tunnel.log. The dashboard's network_info
# module parses the latest URL from that file.

PROJECT_DIR="/home/bacadasa/tomato-sorter"
LOG_DIR="$PROJECT_DIR/data/logs"
LOG_FILE="$LOG_DIR/tunnel.log"
BIN="$PROJECT_DIR/bin/cloudflared"
TARGET_URL="http://localhost:5000"

mkdir -p "$LOG_DIR"

# Truncate the log on each start so the URL parser always finds the
# CURRENT URL, never a stale one from a previous run.
: > "$LOG_FILE"

echo "[$(date '+%F %T')] Starting cloudflared quick tunnel -> $TARGET_URL" >> "$LOG_FILE"

exec "$BIN" tunnel \
    --url "$TARGET_URL" \
    --no-autoupdate \
    --logfile "$LOG_FILE" \
    --loglevel info
