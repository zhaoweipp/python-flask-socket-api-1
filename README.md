# Python Flask Socket Serial 透明转发示例

## 功能

- 串口 -> 后端 -> 前端实时推送
- 前端 -> 后端 -> 串口指令透传
- 串口粘包处理（按分隔符缓冲切包）
- Socket 增强：
  - 心跳检测（前端 ping -> 后端 pong）
  - 自动重连（前端 socket.io reconnection）
  - ACK 消息确认（command 带 msg_id，后端返回 ack）
- 客户端唯一识别码（client_id，浏览器本地存储 + 握手透传）

## 目录

- `app.py`：应用入口
- `serial_manager.py`：串口封装
- `socket_manager.py`：Socket 封装
- `frontend/index.html`：Vue2 示例前端

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 环境变量

- `SERIAL_PORT`：默认 `COM1`
- `SERIAL_BAUDRATE`：默认 `115200`
- `SERIAL_PACKET_DELIMITER`：默认 `\n`
- `PORT`：默认 `5000`

## 事件协议（透明转发，不做业务协议解析）

- 前端发送：`command`
  - `{ "msg_id": "唯一消息ID", "data": "原始字符串" }`
- 后端回执：`ack`
  - `{ "msg_id": "...", "status": "sent|failed", "error": "可选" }`
- 串口推送：`serial_data`
  - `{ "data": "串口报文", "ts": 时间戳 }`
- 心跳：
  - 前端发 `ping`，后端回 `pong`

## 说明

后端不关心命令语义，不做协议解析，仅透明转发。你可以在此基础上自行扩展协议解析逻辑。
