"""Socket.IO 实时消息事件 — 私聊 + 群聊

连接认证：客户端在 auth 参数中传递 JWT token
心跳：ping_interval=25s, ping_timeout=60s
"""

import time
from flask import request
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from jwt_helper import decode_token
from db import execute_query, execute_query_one, execute_insert, execute_update

socketio = SocketIO(
    async_mode="threading",
    cors_allowed_origins="*",
    ping_interval=1,       # 1 秒心跳（轮询兜底时延迟 ≤1s）
    ping_timeout=5,        # 5 秒超时断连
    logger=False,
    engineio_logger=False,
)

# 在线用户追踪 { user_id: { sid, connected_at } }
_online_users: dict[int, dict] = {}


def _get_user_id() -> int | None:
    """从 socket 握手 auth 中提取 user_id"""
    try:
        token = request.args.get("token", "")
        if not token:
            # 也尝试从 headers 获取
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        if not token:
            return None
        payload = decode_token(token)
        return payload.get("user_id") if payload else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
# 连接 / 断开
# ═══════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    user_id = _get_user_id()
    if not user_id:
        disconnect()
        return False
    _online_users[user_id] = {
        "sid": request.sid,
        "connected_at": time.time(),
    }


@socketio.on("disconnect")
def handle_disconnect():
    user_id = _get_user_id()
    if user_id and user_id in _online_users:
        _online_users.pop(user_id, None)


# ═══════════════════════════════════════════════════════
# 私聊
# ═══════════════════════════════════════════════════════

@socketio.on("private_join")
def handle_private_join(data: dict):
    """用户进入私聊房间（标记在线、标记已读）"""
    user_id = _get_user_id()
    if not user_id:
        return

    other_id = data.get("other_id")
    if not other_id:
        return

    # 加入专属私聊房间
    room = f"private:{min(user_id, other_id)}_{max(user_id, other_id)}"
    join_room(room)

    # 标记已读
    execute_update(
        "UPDATE user_private_messages SET is_read = 1 "
        "WHERE sender_id = %s AND receiver_id = %s AND is_read = 0",
        (other_id, user_id),
    )

    # 通知对方"已读"
    if other_id in _online_users:
        emit("private_read", {"user_id": user_id}, room=room, skip_sid=request.sid)


@socketio.on("private_leave")
def handle_private_leave(data: dict):
    """离开私聊房间"""
    user_id = _get_user_id()
    other_id = data.get("other_id")
    if user_id and other_id:
        room = f"private:{min(user_id, other_id)}_{max(user_id, other_id)}"
        leave_room(room)


@socketio.on("private_send")
def handle_private_send(data: dict):
    """发送私信 → 先推后存，延迟最小化"""
    user_id = _get_user_id()
    if not user_id:
        return

    receiver_id = data.get("receiver_id")
    content = (data.get("content") or "").strip()
    if not receiver_id or not content or receiver_id == user_id:
        return
    # 内容长度限制（防内存攻击）
    if len(content) > 5000:
        content = content[:5000]

    # 生成临时 ID 和时间（不等 DB 返回）
    import datetime, random
    temp_id = int(time.time() * 1000) + random.randint(0, 9999)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = {
        "id": temp_id,
        "sender_id": user_id,
        "receiver_id": receiver_id,
        "content": content,
        "msg_type": "text",
        "created_at": now_str,
    }

    # 步骤1：立即推送（0 延迟）
    room = f"private:{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    emit("private_message", msg, room=room)
    # 通知接收方（独立 socket，给 Messages 列表页接收）
    if receiver_id in _online_users:
        emit("private_message", msg, to=_online_users[receiver_id]["sid"])

    # 步骤2：异步存库（不阻塞推送）
    import threading
    threading.Thread(target=_persist_private_message, args=(user_id, receiver_id, content), daemon=True).start()


def _persist_private_message(sender_id, receiver_id, content):
    """后台异步存储私信到 DB"""
    try:
        execute_insert(
            "INSERT INTO user_private_messages (sender_id, receiver_id, msg_type, content, created_at) "
            "VALUES (%s, %s, 'text', %s, NOW())",
            (sender_id, receiver_id, content),
        )
    except Exception:
        pass  # 静默失败，消息已推送，DB 失败不影响实时体验


# ═══════════════════════════════════════════════════════
# 群聊
# ═══════════════════════════════════════════════════════

@socketio.on("group_join")
def handle_group_join(data: dict):
    """加入群聊房间"""
    user_id = _get_user_id()
    group_id = data.get("group_id")
    if user_id and group_id:
        join_room(f"group:{group_id}")


@socketio.on("group_leave")
def handle_group_leave(data: dict):
    """离开群聊房间"""
    user_id = _get_user_id()
    group_id = data.get("group_id")
    if user_id and group_id:
        leave_room(f"group:{group_id}")


@socketio.on("group_send")
def handle_group_send(data: dict):
    """发送群消息 → 先推后存"""
    user_id = _get_user_id()
    if not user_id:
        return

    group_id = data.get("group_id")
    content = (data.get("content") or "").strip()
    if not group_id or not content:
        return
    if len(content) > 5000:
        content = content[:5000]

    # 生成临时 ID 和时间
    import datetime, random
    temp_id = int(time.time() * 1000) + random.randint(0, 9999)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = {
        "id": temp_id,
        "group_id": group_id,
        "sender_id": user_id,
        "nickname": "",
        "avatar_url": "",
        "content": content,
        "msg_type": "text",
        "created_at": now_str,
    }

    # 步骤1：立即广播到房间 + 推送所有在线用户（<10ms）
    room = f"group:{group_id}"
    emit("group_message", msg, room=room)
    for uid, info in _online_users.items():
        if uid != user_id:
            emit("group_message", msg, to=info["sid"])

    # 步骤2：异步存库
    import threading
    threading.Thread(target=_persist_group_message, args=(group_id, user_id, content), daemon=True).start()


def _persist_group_message(group_id, sender_id, content):
    """后台异步存储群消息到 DB"""
    try:
        member = execute_query_one(
            "SELECT id FROM chat_group_members WHERE group_id = %s AND user_id = %s AND deleted_at IS NULL",
            (group_id, sender_id),
        )
        if not member:
            return
        execute_insert(
            "INSERT INTO chat_messages (group_id, sender_id, msg_type, content, created_at) "
            "VALUES (%s, %s, 'text', %s, NOW())",
            (group_id, sender_id, content),
        )
    except Exception:
        pass
