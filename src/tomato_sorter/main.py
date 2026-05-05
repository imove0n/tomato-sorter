"""Entry point: starts every service in order and runs the Flask app."""
import logging

from . import database
from .arduino_link import ArduinoLink
from .config import SETTINGS
from .conveyor import ConveyorController
from .detector import Detector
from .orchestrator import Orchestrator
from .sensors import SensorService
from .server import create_app


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    log = logging.getLogger("main")

    log.info("Initializing database...")
    database.init_db()
    database.log_event("info", "main", "starting up")

    log.info("Starting detector (camera + NCNN)...")
    detector = Detector()
    detector.start()

    log.info("Starting DHT22 sensor service...")
    sensors = SensorService()
    sensors.start()

    log.info("Connecting to Arduino...")
    arduino = ArduinoLink()
    arduino.start()

    log.info("Starting conveyor controller...")
    conveyor = ConveyorController()
    conveyor.start()

    log.info("Initializing orchestrator...")
    orch = Orchestrator(arduino, detector)
    arduino._on_event = orch.on_ir   # route IR events into orchestrator

    log.info("Starting Flask server...")
    app, sock = create_app(detector, sensors, arduino, orch, conveyor)

    cfg = SETTINGS["server"]
    sock.run(app, host=cfg["host"], port=cfg["port"],
             debug=cfg["debug"], allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
