#!/bin/bash
# Enable the Pi as a WiFi access point for thesis demos.
#
# Phones can connect directly to the Pi — no router needed.
# Default credentials below; change them at the top of the file.
#
# Usage:  sudo bash deploy/hotspot-on.sh
#
# After this runs:
#   SSID:     TomatoSorter
#   Password: tomato123
#   Pi IP:    10.42.0.1
#   Dashboard URL on phone: http://10.42.0.1:5000

set -e

SSID="TomatoSorter"
PASSWORD="tomato123"
IFACE="wlan0"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo."
    exit 1
fi

echo "==> Stopping any existing hotspot connection…"
nmcli connection down TomatoSorter 2>/dev/null || true
nmcli connection delete TomatoSorter 2>/dev/null || true

echo "==> Bringing up hotspot on $IFACE…"
nmcli device wifi hotspot ifname "$IFACE" \
    ssid "$SSID" password "$PASSWORD" \
    con-name TomatoSorter

# Make sure the hotspot uses WPA2-PSK (AES). NetworkManager defaults are
# usually fine, but we lock it explicitly so older phones connect smoothly.
nmcli connection modify TomatoSorter wifi-sec.key-mgmt wpa-psk
nmcli connection modify TomatoSorter wifi-sec.pairwise ccmp
nmcli connection modify TomatoSorter wifi-sec.group ccmp
nmcli connection modify TomatoSorter wifi-sec.proto rsn
nmcli connection up TomatoSorter

# Show final state
echo
echo "==> Hotspot active. Connection details:"
echo "    SSID:     $SSID"
echo "    Password: $PASSWORD"
PI_IP=$(ip -4 -o addr show dev "$IFACE" | awk '{print $4}' | cut -d/ -f1 | head -1)
echo "    Pi IP:    ${PI_IP:-unknown}"
echo "    URL:      http://${PI_IP:-raspberrypi.local}:5000"
echo
echo "==> Phones can now connect to '$SSID' and open the URL above."
echo "    To turn the hotspot OFF later:  sudo bash deploy/hotspot-off.sh"
