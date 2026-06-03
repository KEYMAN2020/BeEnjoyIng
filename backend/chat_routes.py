"""聊天模块路由 — 6 个 API 端点

路由前缀: /api/v1/chat
"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from operation_log import log_operation

chat_bp = Blueprint("chat", __name__)


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


# ═══════════════════════════════════════════════════════
# 1. 我的聊天群列表
# ═══════════════════════════════════════════════════════
@chat_bp.get("/groups")
@require_auth
def my_groups():
    """获取我的聊天群列表"""
    user_id = g.current_user["user_id"]

    rows = execute_query(
        """SELECT g.id, g.name, g.avatar, g.activity_id, g.member_count, g.status,
                  gm.last_read_at, gm.is_muted,
                  (SELECT content FROM chat_messages WHERE group_id = g.id ORDER BY created_at DESC LIMIT 1) AS last_message,
                  (SELECT created_at FROM chat_messages WHERE group_id = g.id ORDER BY created_at DESC LIMIT 1) AS last_message_at,
                  (SELECT COUNT(*) FROM chat_messages WHERE group_id = g.id AND created_at > COALESCE(gm.last_read_at, '1970-01-01')) AS unread_count
           FROM chat_groups g
           JOIN chat_group_members gm ON gm.group_id = g.id
           WHERE gm.user_id = %s AND g.deleted_at IS NULL AND gm.deleted_at IS NULL AND g.status = 'active'
           ORDER BY last_message_at DESC""",
        (user_id,),
    )

    return success({
        "groups": [{
            "id": r["id"],
            "name": r["name"],
            "avatar": r.get("avatar", ""),
            "activity_id": r.get("activity_id"),
            "member_count": r["member_count"],
            "is_muted": bool(r["is_muted"]),
            "last_message": r.get("last_message", ""),
            "last_message_at": r["last_message_at"].isoformat() if r.get("last_message_at") and hasattr(r["last_message_at"], "isoformat") else r.get("last_message_at"),
            "unread_count": r["unread_count"],
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 2. 创建聊天群
# ═══════════════════════════════════════════════════════
@chat_bp.post("/groups")
@require_auth
def create_group():
    """创建聊天群

    请求: {name, avatar?, activity_id?, member_ids?}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    name = data.get("name", "")
    if not name:
        return error("请填写群名称", 400)

    group_id = execute_insert(
        """INSERT INTO chat_groups
           (name, avatar, activity_id, captain_id, member_count, status, created_at, updated_at)
           VALUES (%s, %s, %s, %s, 1, 'active', NOW(), NOW())""",
        (name, data.get("avatar", ""), data.get("activity_id"), user_id),
    )

    # 添加创建者为成员
    execute_insert(
        "INSERT INTO chat_group_members (group_id, user_id, joined_at, created_at) VALUES (%s, %s, NOW(), NOW())",
        (group_id, user_id),
    )

    # 添加其他成员
    member_ids = data.get("member_ids", [])
    if member_ids and isinstance(member_ids, list):
        for mid in member_ids:
            if mid != user_id:
                execute_insert(
                    "INSERT INTO chat_group_members (group_id, user_id, joined_at, created_at) VALUES (%s, %s, NOW(), NOW())",
                    (group_id, mid),
                )
        execute_update(
            "UPDATE chat_groups SET member_count = %s WHERE id = %s",
            (len(member_ids) + 1, group_id),
        )

    log_operation(
        operator_id=user_id,
        action="CREATE_CHAT_GROUP",
        target_type="chat_group",
        target_id=group_id,
        detail=f"创建群聊: {name}",
        ip_address=_get_ip(),
    )

    return success({"group_id": group_id}, "群聊已创建"), 201


# ═══════════════════════════════════════════════════════
# 3. 获取群消息
# ═══════════════════════════════════════════════════════
@chat_bp.get("/groups/<int:group_id>/messages")
@require_auth
def get_messages(group_id):
    """获取群聊消息（分页）

    查询参数: before_id (上一页最后一条消息的ID), limit (默认50)
    """
    user_id = g.current_user["user_id"]

    # 检查是否为成员
    member = execute_query_one(
        "SELECT id FROM chat_group_members WHERE group_id = %s AND user_id = %s AND deleted_at IS NULL",
        (group_id, user_id),
    )
    if not member:
        return error("您不是该群成员", 403)

    before_id = request.args.get("before_id", type=int)
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 200)

    if before_id:
        sql = """SELECT m.*, u.nickname, u.avatar_url
                 FROM chat_messages m
                 JOIN users u ON u.id = m.sender_id
                 WHERE m.group_id = %s AND m.id < %s
                 ORDER BY m.created_at DESC
                 LIMIT %s"""
        params = [group_id, before_id, limit]
    else:
        sql = """SELECT m.*, u.nickname, u.avatar_url
                 FROM chat_messages m
                 JOIN users u ON u.id = m.sender_id
                 WHERE m.group_id = %s
                 ORDER BY m.created_at DESC
                 LIMIT %s"""
        params = [group_id, limit]

    rows = execute_query(sql, params)
    rows.reverse()  # 按时间正序返回

    return success({
        "messages": [{
            "id": r["id"],
            "sender_id": r["sender_id"],
            "nickname": r["nickname"],
            "avatar_url": r.get("avatar_url", ""),
            "msg_type": r["msg_type"],
            "content": r.get("content", ""),
            "voice_url": r.get("voice_url"),
            "voice_duration": r.get("voice_duration"),
            "image_url": r.get("image_url"),
            "is_announcement": bool(r["is_announcement"]),
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in rows],
        "has_more": len(rows) >= limit,
    })


# ═══════════════════════════════════════════════════════
# 4. 发送消息
# ═══════════════════════════════════════════════════════
@chat_bp.post("/groups/<int:group_id>/messages")
@require_auth
def send_message(group_id):
    """发送群消息

    请求: {content?, msg_type?, voice_url?, voice_duration?, image_url?}
    """
    user_id = g.current_user["user_id"]

    member = execute_query_one(
        "SELECT id FROM chat_group_members WHERE group_id = %s AND user_id = %s AND deleted_at IS NULL",
        (group_id, user_id),
    )
    if not member:
        return error("您不是该群成员", 403)

    data = request.get_json(silent=True) or {}
    msg_type = data.get("msg_type", "text")

    if msg_type == "text":
        content = data.get("content", "")
        if not content:
            return error("消息内容不能为空", 400)
    elif msg_type == "voice":
        if not data.get("voice_url"):
            return error("请提供语音文件地址", 400)
        content = data.get("content", "")
    elif msg_type == "image":
        if not data.get("image_url"):
            return error("请提供图片地址", 400)
        content = data.get("content", "")
    else:
        return error("不支持的消息类型", 400)

    msg_id = execute_insert(
        """INSERT INTO chat_messages
           (group_id, sender_id, msg_type, content, voice_url, voice_duration, image_url, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (
            group_id, user_id, msg_type, content,
            data.get("voice_url"), data.get("voice_duration"),
            data.get("image_url"),
        ),
    )

    return success({"message_id": msg_id}, "发送成功"), 201


# ═══════════════════════════════════════════════════════
# 5. 标记已读
# ═══════════════════════════════════════════════════════
@chat_bp.post("/groups/<int:group_id>/read")
@require_auth
def mark_read(group_id):
    """标记群消息为已读"""
    user_id = g.current_user["user_id"]

    execute_update(
        "UPDATE chat_group_members SET last_read_at = NOW() WHERE group_id = %s AND user_id = %s",
        (group_id, user_id),
    )

    return success(None, "已标记为已读")


# ═══════════════════════════════════════════════════════
# 6. 退出群聊
# ═══════════════════════════════════════════════════════
@chat_bp.delete("/groups/<int:group_id>/leave")
@require_auth
def leave_group(group_id):
    """退出群聊（软删除）"""
    user_id = g.current_user["user_id"]

    execute_update(
        "UPDATE chat_group_members SET deleted_at = NOW() WHERE group_id = %s AND user_id = %s",
        (group_id, user_id),
    )

    # 更新成员数
    count = execute_query_one(
        "SELECT COUNT(*) AS cnt FROM chat_group_members WHERE group_id = %s AND deleted_at IS NULL",
        (group_id,),
    )
    execute_update(
        "UPDATE chat_groups SET member_count = %s WHERE id = %s",
        (count["cnt"], group_id),
    )

    log_operation(
        operator_id=user_id,
        action="LEAVE_GROUP",
        target_type="chat_group",
        target_id=group_id,
        ip_address=_get_ip(),
    )

    return success(None, "已退出群聊")
