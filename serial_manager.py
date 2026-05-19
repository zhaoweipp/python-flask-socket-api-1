import threading
import time
from typing import Callable, Optional

import serial


class SerialManager:
    """Serial layer: transparent forwarding + sticky packet handling by delimiter buffering."""

    def __init__(self, port: str, baudrate: int, packet_delimiter: bytes = b"\n"):
        self.port = port
        self.baudrate = baudrate
        self.packet_delimiter = packet_delimiter
        self._serial: Optional[serial.Serial] = None
        self._on_packet: Optional[Callable[[bytes], None]] = None
        self._buffer = bytearray()
        self._running = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def set_on_packet(self, callback: Callable[[bytes], None]) -> None:
        self._on_packet = callback

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()

    def write(self, data: bytes) -> None:
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise RuntimeError("Serial port is not open")
            self._serial.write(data)

    def _ensure_connected(self) -> bool:
        if self._serial and self._serial.is_open:
            return True
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.2)
            return True
        except Exception:
            time.sleep(1)
            return False

    def _read_loop(self) -> None:
        while self._running:
            if not self._ensure_connected():
                continue
            try:
                chunk = self._serial.read(1024)
                if chunk:
                    self._buffer.extend(chunk)
                    self._drain_buffer()
            except Exception:
                if self._serial:
                    self._serial.close()
                time.sleep(1)

    def _drain_buffer(self) -> None:
        if not self.packet_delimiter:
            return
        while True:
            idx = self._buffer.find(self.packet_delimiter)
            if idx < 0:
                break
            end = idx + len(self.packet_delimiter)
            packet = bytes(self._buffer[:end])
            del self._buffer[:end]
            if self._on_packet:
                self._on_packet(packet)
