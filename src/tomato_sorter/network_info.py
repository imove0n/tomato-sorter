"""Network access helpers — detect Pi's IP / hostname / hotspot state
and generate QR codes for phone access to the dashboard."""
import base64
import io
import socket
import subprocess
from typing import Optional

import qrcode

DASHBOARD_PORT = 5000


def get_lan_ip() -> Optional[str]:
    """Return the Pi's LAN IP address (the one a phone on the same network
    would use). Falls back to None if no network detected."""
    try:
        # Trick: open a UDP socket to a public IP. No packets actually sent;
        # this just makes the OS pick the right outbound interface.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Hotspot mode — no internet route. Try the wlan0 interface directly.
        try:
            out = subprocess.check_output(
                ["ip", "-4", "-o", "addr", "show", "dev", "wlan0"],
                timeout=2
            ).decode()
            # Format: "3: wlan0    inet 10.42.0.1/24 brd 10.42.0.255 ..."
            for tok in out.split():
                if "." in tok and "/" in tok:
                    return tok.split("/")[0]
        except Exception:
            pass
        return None


def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "raspberrypi"


def is_hotspot_active() -> bool:
    """True if NetworkManager has an active hotspot connection on wlan0."""
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device"],
            timeout=2,
        ).decode()
        # When hotspot is active, nmcli reports the connection name (we use 'TomatoSorter')
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[0] == "wifi" and parts[1] == "connected":
                # Check if connection is our hotspot (named TomatoSorter)
                conn = subprocess.check_output(
                    ["nmcli", "-t", "-f", "802-11-wireless.mode", "connection", "show", parts[2]],
                    timeout=2,
                ).decode().strip()
                if "ap" in conn.lower():
                    return True
        return False
    except Exception:
        return False


def get_hotspot_ssid() -> Optional[str]:
    """Returns the SSID of the active hotspot if one is running, else None."""
    if not is_hotspot_active():
        return None
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "ACTIVE,SSID,MODE", "dev", "wifi"],
            timeout=2,
        ).decode()
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[0] == "yes":
                return parts[1]
    except Exception:
        pass
    return None


def network_summary() -> dict:
    """Single dict consumed by the dashboard for the Phone Access panel."""
    ip       = get_lan_ip()
    hostname = get_hostname()
    hotspot  = is_hotspot_active()
    ssid     = get_hotspot_ssid() if hotspot else None

    urls = {}
    if ip:
        urls["ip"] = f"http://{ip}:{DASHBOARD_PORT}"
    if hostname:
        urls["hostname"] = f"http://{hostname}.local:{DASHBOARD_PORT}"

    return {
        "ip":       ip,
        "hostname": hostname,
        "hotspot":  hotspot,
        "ssid":     ssid,
        "urls":     urls,
    }


def make_qr_png_base64(data: str, box_size: int = 6) -> str:
    """Build a QR code as a base64-encoded PNG string ready for an <img src>."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def make_wifi_join_qr(ssid: str, password: str, security: str = "WPA") -> str:
    """QR code that phones recognize as 'join this WiFi network' (no manual typing)."""
    # Standard format supported by iOS/Android camera apps:
    #   WIFI:T:<WPA|WEP|nopass>;S:<ssid>;P:<password>;H:<true|false>;;
    payload = f"WIFI:T:{security};S:{ssid};P:{password};H:false;;"
    return make_qr_png_base64(payload, box_size=7)
