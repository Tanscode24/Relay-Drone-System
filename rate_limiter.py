"""
rate_limiter.py

Simple per-key token-bucket rate limiter used to cap how often
non-critical (telemetry) message types are forwarded onto a given link.

Each SerialLink owns its own RateLimiterRegistry, so the same message
type can have independent rate state on each link (e.g. GLOBAL_POSITION_INT
can go out fast on the wired Pixhawk link but capped on the wireless
ground link).
"""

import time
import threading


class TokenBucket:

    def __init__(self, rate_hz: float):
        self.rate_hz = max(rate_hz, 0.01)
        self.min_interval = 1.0 / self.rate_hz
        self._last_sent = 0.0
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last_sent >= self.min_interval:
                self._last_sent = now
                return True
            return False

    def update_rate(self, rate_hz: float):
        with self._lock:
            self.rate_hz = max(rate_hz, 0.01)
            self.min_interval = 1.0 / self.rate_hz

class RateLimiterRegistry:
    def __init__(self):
        self._buckets = {}
        self._lock = threading.Lock()

    def allow(self, msg_type: str, rate_hz: float) -> bool:
        bucket = self._buckets.get(msg_type)
        if bucket is None:
            with self._lock:
                bucket = self._buckets.get(msg_type)
                if bucket is None:
                    bucket = TokenBucket(rate_hz)
                    self._buckets[msg_type] = bucket
        else:
            bucket.update_rate(rate_hz)
        return bucket.allow()
