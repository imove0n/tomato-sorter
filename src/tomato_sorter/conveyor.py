"""Simple BTS7960 conveyor controller for Raspberry Pi GPIO."""
import logging

try:
    from gpiozero import OutputDevice
except Exception:  # pragma: no cover - hardware import depends on target device
    OutputDevice = None

from .config import SETTINGS


class ConveyorController:
    def __init__(self):
        self._cfg = SETTINGS["conveyor"]
        self._log = logging.getLogger("conveyor")
        self._rpwm = None
        self._lpwm = None
        self._state = "STOPPED"

    def start(self):
        if OutputDevice is None:
            self._log.warning("gpiozero unavailable; conveyor controls disabled")
            return
        self._rpwm = OutputDevice(self._cfg["rpwm_gpio_pin"], active_high=True, initial_value=False)
        self._lpwm = OutputDevice(self._cfg["lpwm_gpio_pin"], active_high=True, initial_value=False)
        self.stop()

    def stop(self):
        if self._rpwm:
            self._rpwm.off()
        if self._lpwm:
            self._lpwm.off()
        self._state = "STOPPED"

    def forward(self):
        if self._lpwm:
            self._lpwm.off()
        if self._rpwm:
            self._rpwm.on()
        self._state = "FORWARD"

    def reverse(self):
        if self._rpwm:
            self._rpwm.off()
        if self._lpwm:
            self._lpwm.on()
        self._state = "REVERSE"

    def state(self) -> str:
        return self._state
