# signals were getting duplicated, to many false signals were sending via telementry, to filter & to fix that.

import threading
import time
from collections import OrderedDict

from config import DEDUP_CACHE_TTL_SEC, DEDUP_CACHE_MAX_ENTRIES


class Deduplicator:
    def __init__(self, ttl=DEDUP_CACHE_TTL_SEC, max_entries=DEDUP_CACHE_MAX_ENTRIES):
        self._ttl = ttl
        self._max_entries = max_entries
        self._seen = OrderedDict()   # fingerprint -> timestamp, oldest first
        self._lock = threading.Lock()

    @staticmethod
    def fingerprint(msg) -> bytes:
        return bytes(msg.get_msgbuf())

    def is_duplicate(self, msg) -> bool:
        fp = self.fingerprint(msg)
        now = time.monotonic()

        with self._lock:
            self._evict_expired(now)

            last_seen = self._seen.get(fp)
            if last_seen is not None and (now - last_seen) < self._ttl:
                return True

            self._seen[fp] = now
            self._seen.move_to_end(fp)

            if len(self._seen) > self._max_entries:
                self._seen.popitem(last=False)

            return False

    def _evict_expired(self, now):
        while self._seen:
            fp, ts = next(iter(self._seen.items()))
            if now - ts > self._ttl:
                self._seen.popitem(last=False)
            else:
                break
