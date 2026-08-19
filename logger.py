# For logging purpose

import logging
import logging.handlers
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "mavlink_relay.log")

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-16s | %(message)s"

def _build_logger() -> logging.Logger:
    log = logging.getLogger("MAVLinkRouter")
    log.setLevel(logging.INFO)
    if log.handlers:
        return log
    formatter = logging.Formatter(_FORMAT)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log.addHandler(console)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
    except OSError:
        log.warning("Could not open log file, continuing with console logging only")
    return log
logger = _build_logger()
def get_link_logger(link_name: str) -> logging.Logger:
    """Child logger so per-link messages are easy to filter/grep."""
    return logger.getChild(link_name)
