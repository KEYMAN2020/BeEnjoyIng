"""Socket.IO + Werkzeug (WebSocket via simple-websocket) 生产入口

启动命令:
  python wsgi_socketio.py
  或指定端口: PORT=5003 python wsgi_socketio.py
"""

import os
from app import app
from socket_events import socketio

# 将 Socket.IO 挂载到 Flask
socketio.init_app(app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5003))
    print(f"BeEnjoyIng API (Socket.IO WebSocket) 启动在 0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
