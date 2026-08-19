# Earlier, the signal of each system id was going to every telementry, and then if the system id of the signal & telementry pixhawk matches then it acts, but now the signal of each system id is going to only the telementry which has the same system id, so that the telementry of other system id does not act on the signal of other system id.

import threading
import time

from config import SYSTEM_TIMEOUT_SEC


class DroneManager:
    def __init__(self):
        self._table = {}  
        self._lock = threading.Lock()

    def observe(self, sysid: int, compid: int, link_name: str):
        with self._lock:
            self._table[sysid] = {
                "link": link_name,
                "compid": compid,
                "last_seen": time.monotonic(),
            }

    def link_for_system(self, sysid: int):
        """Return the link name a system was last heard on, or None if
        unknown or stale (hasn't sent a heartbeat within SYSTEM_TIMEOUT_SEC).
        """
        with self._lock:
            entry = self._table.get(sysid)
            if entry is None:
                return None
            if time.monotonic() - entry["last_seen"] > SYSTEM_TIMEOUT_SEC:
                return None
            return entry["link"]

    def known_systems(self):
        """Return a snapshot of currently-live systems, for diagnostics."""
        with self._lock:
            now = time.monotonic()
            return {
                sysid: dict(e) for sysid, e in self._table.items()
                if now - e["last_seen"] <= SYSTEM_TIMEOUT_SEC
            }
