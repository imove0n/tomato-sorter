#!/bin/bash
# Disable the hotspot and reconnect to the previous WiFi network.
#
# Usage:  sudo bash deploy/hotspot-off.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo."
    exit 1
fi

echo "==> Bringing down hotspot…"
nmcli connection down TomatoSorter 2>/dev/null || true
nmcli connection delete TomatoSorter 2>/dev/null || true

echo "==> Re-scanning for known WiFi networks…"
nmcli device wifi rescan 2>/dev/null || true
sleep 2

# Try to reconnect to whatever WiFi profile was last used.
LAST=$(nmcli -t -f NAME,TYPE,AUTOCONNECT connection show | awk -F: '$2=="802-11-wireless" && $3=="yes" {print $1; exit}')
if [ -n "$LAST" ]; then
    echo "==> Activating saved WiFi profile: $LAST"
    nmcli connection up "$LAST" || true
fi

echo
echo "==> Done. Current connection:"
nmcli -t -f NAME,DEVICE connection show --active | grep -v ':lo$' || echo "(none)"
