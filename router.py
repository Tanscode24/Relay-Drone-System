import signal
import sys
import time

from config import LINKS, NODE_NAME
from logger import logger
from serial_link import SerialLink
from dedup import Deduplicator
from drone_manager import DroneManager
from routing_manager import RoutingManager


class RelayRouter:
    def __init__(self):
        self.dedup = Deduplicator()
        self.drones = DroneManager()
        self.links = [SerialLink(cfg, self._on_message) for cfg in LINKS]
        self.routing = RoutingManager(self.links, self.drones)

    def start(self):
        logger.info("Starting MAVLink relay router (%s)", NODE_NAME)
        for link in self.links:
            link.start()
        logger.info("All links starting: %s", [l.name for l in self.links])

    def stop(self):
        logger.info("Stopping router...")
        for link in self.links:
            link.stop()

    def _on_message(self, source_link, msg):
        if msg.get_type() == "HEARTBEAT":
            self.drones.observe(
                msg.get_srcSystem(), msg.get_srcComponent(), source_link.name
            )

        if self.dedup.is_duplicate(msg):
            return
        for dest_link in self.routing.destinations_for(source_link, msg):
            dest_link.send(msg)

    def run_forever(self):
        self.start()
        def _handle_signal(signum, frame):
            self.stop()
            sys.exit(0)
        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
        logger.info("Bridge running...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    RelayRouter().run_forever()
