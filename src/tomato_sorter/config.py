"""Loads config/settings.yaml once and exposes it as a global."""
from pathlib import Path
import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH  = _PROJECT_ROOT / "config" / "settings.yaml"


def load() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


SETTINGS = load()
PROJECT_ROOT = _PROJECT_ROOT


def servo_angles() -> dict:
    """Load calibrated servo angles from config/servo_angles.json."""
    import json
    p = PROJECT_ROOT / "config" / "servo_angles.json"
    return json.loads(p.read_text()) if p.exists() else {}
