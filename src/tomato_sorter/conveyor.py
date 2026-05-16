"""BTS7960 conveyor controller for Raspberry Pi GPIO.

Uses PWM on RPWM/LPWM so speed can be set from 0-100%. The same
direction calls (forward/reverse) respect whatever speed was last
set via set_speed().
"""
import logging

try:
    from gpiozero import PWMOutputDevice
except Exception:  # pragma: no cover - hardware import depends on target device
    PWMOutputDevice = None

from .config import SETTINGS


class ConveyorController:
    def __init__(self):
        self._cfg = SETTINGS["conveyor"]
        self._log = logging.getLogger("conveyor")
        self._rpwm = None
        self._lpwm = None
        self._state = "STOPPED"
        self._speed = 1.0      # 0.0-1.0, default full speed

    def start(self):
        if PWMOutputDevice is None:
            self._log.warning("gpiozero unavailable; conveyor controls disabled")
            return
        # 1 kHz PWM is plenty for a BTS7960 driver.
        self._rpwm = PWMOutputDevice(self._cfg["rpwm_gpio_pin"], frequency=1000, initial_value=0.0)
        self._lpwm = PWMOutputDevice(self._cfg["lpwm_gpio_pin"], frequency=1000, initial_value=0.0)
        self.stop()

    def stop(self):
        if self._rpwm: self._rpwm.value = 0.0
        if self._lpwm: self._lpwm.value = 0.0
        self._state = "STOPPED"

    def forward(self):
        if self._lpwm: self._lpwm.value = 0.0
        if self._rpwm: self._rpwm.value = self._speed
        self._state = "FORWARD"

    def reverse(self):
        if self._rpwm: self._rpwm.value = 0.0
        if self._lpwm: self._lpwm.value = self._speed
        self._state = "REVERSE"

    def set_speed(self, percent):
        """Set conveyor speed as 0-100 (clamped). Applies live to whichever
        direction is currently running."""
        percent = max(0.0, min(100.0, float(percent)))
        self._speed = percent / 100.0
        if self._state == "FORWARD" and self._rpwm:
            self._rpwm.value = self._speed
        elif self._state == "REVERSE" and self._lpwm:
            self._lpwm.value = self._speed

    def speed_percent(self) -> float:
        return round(self._speed * 100.0, 1)

    def state(self) -> str:
        return self._state
