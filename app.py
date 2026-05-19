import os
from apiflask import APIFlask
from flask import send_from_directory
from flask_socketio import SocketIO

from serial_manager import SerialManager
from socket_manager import SocketManager


app = APIFlask(__name__, static_folder="frontend")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=25, ping_timeout=60)

serial_manager = SerialManager(
    port=os.environ.get("SERIAL_PORT", "COM1"),
    baudrate=int(os.environ.get("SERIAL_BAUDRATE", "115200")),
    packet_delimiter=os.environ.get("SERIAL_PACKET_DELIMITER", "\n").encode(),
)
socket_manager = SocketManager(socketio=socketio, serial_manager=serial_manager)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.get("/<path:path>")
def assets(path: str):
    return send_from_directory("frontend", path)


def main() -> None:
    serial_manager.start()
    socket_manager.register_handlers()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))


if __name__ == "__main__":
    main()
