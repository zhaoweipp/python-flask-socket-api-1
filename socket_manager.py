import time
import uuid
from typing import Dict

from flask import request


class SocketManager:
    """Socket layer: client id, heartbeat, reconnect support hints, and ACK mechanism."""

    def __init__(self, socketio, serial_manager):
        self.socketio = socketio
        self.serial_manager = serial_manager
        self.clients: Dict[str, dict] = {}
        self.serial_manager.set_on_packet(self._on_serial_packet)

    def register_handlers(self) -> None:
        @self.socketio.on("connect")
        def on_connect():
            sid = request.sid
            client_id = request.args.get("client_id") or str(uuid.uuid4())
            self.clients[sid] = {"client_id": client_id, "last_seen": time.time()}
            self.socketio.emit("connected", {"client_id": client_id}, room=sid)

        @self.socketio.on("disconnect")
        def on_disconnect():
            sid = request.sid
            self.clients.pop(sid, None)

        @self.socketio.on("ping")
        def on_ping(payload=None):
            sid = request.sid
            if sid in self.clients:
                self.clients[sid]["last_seen"] = time.time()
            self.socketio.emit("pong", payload or {"ts": int(time.time() * 1000)}, room=sid)

        @self.socketio.on("command")
        def on_command(payload):
            sid = request.sid
            msg_id = payload.get("msg_id") if isinstance(payload, dict) else None
            raw = payload.get("data", "") if isinstance(payload, dict) else ""
            data = raw.encode() if isinstance(raw, str) else bytes(raw)
            try:
                self.serial_manager.write(data)
                self.socketio.emit("ack", {"msg_id": msg_id, "status": "sent"}, room=sid)
            except Exception as exc:
                self.socketio.emit(
                    "ack", {"msg_id": msg_id, "status": "failed", "error": str(exc)}, room=sid
                )

    def _on_serial_packet(self, packet: bytes) -> None:
        payload = {"data": packet.decode(errors="ignore"), "ts": int(time.time() * 1000)}
        self.socketio.emit("serial_data", payload)
