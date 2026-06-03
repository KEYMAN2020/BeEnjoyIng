"""通知模块路由 — 3 个 API 端点

路由前缀: /api/v1/notifications
"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_update
from auth_decorator import require_auth

notification_bp = Blueprint("notifications", __name__)


# ═══════════════════════════════════════════════════════
# 1. 通知列表
# ═══════════════════════════════════════════════════════
@notification_bp.get("")
@require_auth
def list_notifications():
    """获取通知列表

    查询参数: type, is_read, page, per_page
    """
    user_id = g.current_user["user_id"]
    notif_type = request.args.get("type", "")
    is_read = request.args.get("is_read", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    conditions = ["n.user_id = %s"]
    params = [user_id]

    if notif_type:
        conditions.append("n.type = %s")
        params.append(notif_type)
    if is_read is not None:
        conditions.append("n.is_read = %s")
        params.append(is_read)

    where = " AND ".join(conditions)

    count_sql = f"SELECT COUNT(*) AS total FROM notifications n WHERE {where}"
    total = execute_query_one(count_sql, params)["total"]

    offset = (page - 1) * per_page
    sql = f"""SELECT * FROM notifications n
              WHERE {where}
              ORDER BY n.created_at DESC
              LIMIT %s OFFSET %s"""
    rows = execute_query(sql, params + [per_page, offset])

    return success({
        "notifications": [{
            "id": r["id"],
            "type": r["type"],
            "title": r["title"],
            "content": r.get("content", ""),
            "ref_type": r.get("ref_type"),
            "ref_id": r.get("ref_id"),
            "is_read": bool(r["is_read"]),
            "read_at": r["read_at"].isoformat() if r.get("read_at") and hasattr(r["read_at"], "isoformat") else r.get("read_at"),
            "channel": r.get("channel", "in_app"),
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "unread_count": execute_query_one(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )["cnt"],
    })


# ═══════════════════════════════════════════════════════
# 2. 标记已读
# ═══════════════════════════════════════════════════════
@notification_bp.put("/<int:notification_id>/read")
@require_auth
def mark_notification_read(notification_id):
    """标记单条通知为已读"""
    user_id = g.current_user["user_id"]

    notif = execute_query_one(
        "SELECT id FROM notifications WHERE id = %s AND user_id = %s",
        (notification_id, user_id),
    )
    if not notif:
        return error("通知不存在", 404)

    execute_update(
        "UPDATE notifications SET is_read = 1, read_at = NOW() WHERE id = %s",
        (notification_id,),
    )

    return success(None, "已标记为已读")


# ═══════════════════════════════════════════════════════
# 3. 全部已读
# ═══════════════════════════════════════════════════════
@notification_bp.post("/read-all")
@require_auth
def mark_all_read():
    """标记所有通知为已读"""
    user_id = g.current_user["user_id"]

    execute_update(
        "UPDATE notifications SET is_read = 1, read_at = NOW() WHERE user_id = %s AND is_read = 0",
        (user_id,),
    )

    return success(None, "全部已标记为已读")
