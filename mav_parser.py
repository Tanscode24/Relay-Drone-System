# Mavlink decoder
from pymavlink.dialects.v20 import common as mavlink2

from config import DEBUG_PRINT_PACKETS
from logger import get_link_logger


class MAVLinkParser:
    def __init__(self, link_name: str):
        self.parser = mavlink2.MAVLink(None)
        self._log = get_link_logger(link_name)

    def feed(self, data: bytes):
        """Feed raw bytes in, yield fully decoded MAVLink message objects.

        Corrupted / incomplete bytes are silently discarded (matches the
        original implementation) -- MAVLink framing self-recovers at the
        next valid start byte.
        """
        for b in data:
            try:
                msg = self.parser.parse_char(bytes([b]))
            except Exception:
                continue

            if msg is None:
                continue

            if DEBUG_PRINT_PACKETS:
                self._debug_log(msg)

            yield msg

    def _debug_log(self, msg):
        self._log.debug(
            "type=%s src=%s/%s seq=%s",
            msg.get_type(), msg.get_srcSystem(), msg.get_srcComponent(), msg.get_seq(),
        )
