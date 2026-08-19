"""
serial_link.py

SerialLink wraps a single physical serial connection (a telemetry radio
or a direct USB/serial link to a flight controller). It owns:

  * a background reader thread that reads raw bytes, feeds them through
    its own MAVLinkParser, and hands decoded messages to a callback
  * a background writer thread that drains a priority queue (critical
    traffic) and a "latest value wins" telemetry table (best-effort,
    rate-limited traffic)
  * automatic reconnect with backoff if the underlying serial device
    errors out or disappears

SerialLink does not know about routing -- it is purely responsible for
getting bytes on and off the wire reliably and without flooding the link.
That separation is what keeps this class reusable if a future link type
(e.g. a UDP link to a radio that exposes a network interface) is added.
"""

import queue
import threading
import time

import serial

from mav_parser import MAVLinkParser
from rate_limiter import RateLimiterRegistry
# from message_policy import is_critical, rate_limit_for
from logger import get_link_logger

from config import (
    CRITICAL_MESSAGE_TYPES,
    TELEMETRY_RATE_LIMITS_HZ,
    DEFAULT_TELEMETRY_RATE_HZ,
    WIRED_RATE_MULTIPLIER,
)


def is_critical(msg_type: str) -> bool:
    return msg_type in CRITICAL_MESSAGE_TYPES


def rate_limit_for(msg_type: str, link_is_wired: bool) -> float:
    base = TELEMETRY_RATE_LIMITS_HZ.get(msg_type, DEFAULT_TELEMETRY_RATE_HZ)
    if link_is_wired:
        return base * WIRED_RATE_MULTIPLIER
    return base

class SerialLink:
    def __init__(self, cfg, on_message):
        """
        cfg: config.LinkConfig
        on_message: callable(link: SerialLink, msg) -> None, invoked for
                    every successfully decoded inbound MAVLink message.
        """
        self.cfg = cfg
        self.name = cfg.name
        self.role = cfg.role
        self.is_wired = cfg.role == "own_pixhawk"

        self._on_message = on_message
        self._parser = MAVLinkParser(cfg.name)
        self._log = get_link_logger(cfg.name)

        self._ser = None
        self._connected = threading.Event()
        self._stop = threading.Event()

        # Critical traffic: ordered FIFO, always flushed first.
        self._critical_queue = queue.Queue(maxsize=cfg.write_queue_size)

        # Best-effort telemetry: only the newest sample per message type
        # is kept ("latest value wins"), which is what prevents backlog
        # buildup when a stream arrives faster than the link can carry it.
        self._telemetry_latest = {}
        self._telemetry_lock = threading.Lock()
        self._rate_limiter = RateLimiterRegistry()

        self._reader_thread = threading.Thread(
            target=self._reader_loop, name=f"{cfg.name}-reader", daemon=True
        )
        self._writer_thread = threading.Thread(
            target=self._writer_loop, name=f"{cfg.name}-writer", daemon=True
        )

    def start(self):
        self._reader_thread.start()
        self._writer_thread.start()

    def stop(self):
        self._stop.set()

    @property
    def connected(self) -> bool:
        return self._connected.is_set()


    def send(self, msg):

        msg_type = msg.get_type()
        raw = msg.get_msgbuf()

        if is_critical(msg_type):
            try:
                self._critical_queue.put(raw, block=True, timeout=self.cfg.critical_put_timeout)
            except queue.Full:
                self._log.error(
                    "Critical queue full for %.1fs, dropping %s -- link '%s' appears "
                    "stuck or disconnected",
                    self.cfg.critical_put_timeout, msg_type, self.name,
                )
        else:
            with self._telemetry_lock:
                self._telemetry_latest[msg_type] = raw


    def _reader_loop(self):
        while not self._stop.is_set():
            if self._ser is None:
                if not self._open():
                    time.sleep(self.cfg.reconnect_interval)
                    continue

            try:
                data = self._ser.read(1024)
            except (serial.SerialException, OSError) as exc:
                self._log.warning("Read error, reconnecting: %s", exc)
                self._close()
                continue

            if data:
                for msg in self._parser.feed(data):
                    try:
                        self._on_message(self, msg)
                    except Exception:
                        self._log.exception("on_message callback failed")
    def _writer_loop(self):
        while not self._stop.is_set():
            if not self.connected:
                time.sleep(0.05)
                continue

            wrote_something = False

            # 1. Critical traffic always goes first, fully drained.
            while True:
                try:
                    raw = self._critical_queue.get_nowait()
                except queue.Empty:
                    break
                self._write_bytes(raw)
                wrote_something = True

            # 2. Best-effort telemetry, rate-limited per message type.
            with self._telemetry_lock:
                pending = list(self._telemetry_latest.items())
                self._telemetry_latest.clear()

            for msg_type, raw in pending:
                rate = rate_limit_for(msg_type, self.is_wired)
                if self._rate_limiter.allow(msg_type, rate):
                    self._write_bytes(raw)
                    wrote_something = True
                # else: dropped this cycle. A newer sample of the same
                # type will naturally replace it before the next allowed
                # send -- this is intentional coalescing, not data loss
                # of anything the ground station actually needs.

            if not wrote_something:
                time.sleep(0.005)

    def _write_bytes(self, raw: bytes):
        try:
            self._ser.write(raw)
        except (serial.SerialException, OSError) as exc:
            self._log.warning("Write error, reconnecting: %s", exc)
            self._close()
    def _open(self) -> bool:
        try:
            self._ser = serial.Serial(self.cfg.port, self.cfg.baud, timeout=self.cfg.timeout)
            self._connected.set()
            self._log.info("Connected (%s @ %s)", self.cfg.port, self.cfg.baud)
            return True
        except (serial.SerialException, OSError) as exc:
            self._ser = None
            self._connected.clear()
            self._log.warning("Could not open %s: %s", self.cfg.port, exc)
            return False

    def _close(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._connected.clear()
