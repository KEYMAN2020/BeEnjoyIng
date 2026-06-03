"""用户模块路由 — 14 个 API 端点

路由前缀: /api/v1/users
"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from operation_log import log_operation

users_bp = Blueprint("users", __name__)


# ── 辅助函数 ─────────────────────────────────────────────


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


def _safe_user(user: dict) -> dict:
    """公开安全字段（不含手机号等敏感信息）"""
    return {
        "user_id": user["id"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url", ""),
        "role": user["role"],
    }


def _public_user(user: dict, profile: dict | None = None) -> dict:
    """公开资料"""
    data = {
        "user_id": user["id"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url", ""),
    }
    if profile:
        # 受隐私设置限制
        if not profile.get("ghost_mode") and profile.get("allow_profile_view"):
            data.update({
                "gender": profile.get("gender"),
                "birth_year": profile.get("birth_year"),
                "city": profile.get("city"),
                "bio": profile.get("bio"),
                "interests": profile.get("interests"),
            })
    return data


def _full_user(user: dict, profile: dict | None = None, stats: dict | None = None) -> dict:
    """完整用户信息"""
    data = {
        "user_id": user["id"],
        "phone": user["phone"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url", ""),
        "role": user["role"],
        "is_banned": bool(user["is_banned"]),
        "created_at": str(user["created_at"]) if user.get("created_at") else None,
    }
    if profile:
        data["profile"] = {
            "real_name": profile.get("real_name"),
            "gender": profile.get("gender"),
            "birth_year": profile.get("birth_year"),
            "city": profile.get("city"),
            "district": profile.get("district"),
            "province_code": profile.get("province_code"),
            "city_code": profile.get("city_code"),
            "district_code": profile.get("district_code"),
            "bio": profile.get("bio"),
            "interests": profile.get("interests"),
            "ghost_mode": bool(profile["ghost_mode"]),
            "allow_private_msg": bool(profile["allow_private_msg"]),
            "allow_profile_view": bool(profile["allow_profile_view"]),
        }
    if stats:
        data["stats"] = {
            "vitality": stats["vitality"],
            "activity_count": stats["activity_count"],
            "activity_streak": stats["activity_streak"],
            "friends_count": stats["friends_count"],
            "last_active_at": str(stats["last_active_at"]) if stats.get("last_active_at") else None,
        }
    return data


def _build_dynamic_update(table: str, data: dict, allowed_fields: list, key_field: str, key_value) -> tuple:
    """动态构建 SET 子句，只更新提供的非空字段"""
    updates = []
    params = []
    for field in allowed_fields:
        if field in data and data[field] is not None and data[field] != "":
            updates.append(f"{field} = %s")
            params.append(data[field])
    updates.append("updated_at = NOW()")
    sql = f"UPDATE {table} SET {', '.join(updates)} WHERE {key_field} = %s"
    params.append(key_value)
    return sql, params


# ═══════════════════════════════════════════════════════
# 个人资料
# ═══════════════════════════════════════════════════════

# ── #1 GET /api/v1/users/me ────────────────────────────
@users_bp.get("/me")
@require_auth
def get_my_profile():
    """获取当前登录用户完整信息（users + user_profiles + user_stats 三表联合）"""
    user_id = g.current_user["user_id"]

    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at "
        "FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,)
    )
    if not user:
        return error("用户不存在", 404)

    profile = execute_query_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    stats = execute_query_one("SELECT * FROM user_stats WHERE user_id = %s", (user_id,))

    return success({"user": _full_user(user, profile, stats)})


# ── #2 PUT /api/v1/users/me ────────────────────────────
@users_bp.put("/me")
@require_auth
def update_my_profile_full():
    """完整更新用户资料（users + user_profiles）"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    # 更新 users 表
    user_fields = ["nickname", "avatar_url"]
    user_updates = []
    user_params = []
    for f in user_fields:
        if f in data and data[f] is not None:
            user_updates.append(f"{f} = %s")
            user_params.append(data[f])
    if user_updates:
        user_updates.append("updated_at = NOW()")
        execute_update(
            f"UPDATE users SET {', '.join(user_updates)} WHERE id = %s",
            (*user_params, user_id),
        )

    # 更新 user_profiles 表
    profile_fields = [
        "real_name", "gender", "birth_year", "city", "district",
        "province_code", "city_code", "district_code",
        "bio", "interests", "ghost_mode", "allow_private_msg", "allow_profile_view",
    ]
    profile_updates = []
    profile_params = []
    for f in profile_fields:
        if f in data and data[f] is not None:
            profile_updates.append(f"{f} = %s")
            profile_params.append(data[f])
    if profile_updates:
        profile_updates.append("updated_at = NOW()")
        # 确保 profile 行存在
        existing = execute_query_one("SELECT user_id FROM user_profiles WHERE user_id = %s", (user_id,))
        if existing:
            execute_update(
                f"UPDATE user_profiles SET {', '.join(profile_updates)} WHERE user_id = %s",
                (*profile_params, user_id),
            )
        else:
            profile_params.append(user_id)
            cols = [f.split(" =")[0] for f in profile_updates if "updated_at" not in f] + ["user_id", "updated_at"]
            placeholders = ["%s"] * len(cols)
            execute_insert(
                f"INSERT INTO user_profiles ({', '.join(cols)}) VALUES ({', '.join(placeholders)}, NOW())",
                (*[data.get(f.split()[0]) for f in profile_updates if "updated_at" not in f], user_id),
            )
            # simpler approach for insert
            execute_update("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
            insert_fields = ["user_id", "updated_at"]
            insert_vals = [user_id]
            for f in profile_fields:
                if f in data and data[f] is not None:
                    insert_fields.append(f)
                    insert_vals.append(data[f])
            placeholders = ", ".join(["%s"] * len(insert_fields))
            execute_insert(
                f"INSERT INTO user_profiles ({', '.join(insert_fields)}) VALUES ({placeholders})",
                insert_vals,
            )

    log_operation(user_id, "UPDATE_PROFILE", "user", user_id, "完整更新资料", _get_ip())

    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at "
        "FROM users WHERE id = %s", (user_id,)
    )
    profile = execute_query_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    return success({"user": _full_user(user, profile)})


# ── #3 PATCH /api/v1/users/me ──────────────────────────
@users_bp.patch("/me")
@require_auth
def update_my_profile_partial():
    """部分更新用户资料"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    # users 表
    user_fields = ["nickname", "avatar_url"]
    sql_u, params_u = _build_dynamic_update("users", data, user_fields, "id", user_id)
    if len(params_u) > 1:  # 有实际更新字段（不含 updated_at）
        execute_update(sql_u, params_u)

    # user_profiles 表
    profile_fields = [
        "real_name", "gender", "birth_year", "city", "district",
        "province_code", "city_code", "district_code",
        "bio", "interests", "ghost_mode", "allow_private_msg", "allow_profile_view",
    ]
    sql_p, params_p = _build_dynamic_update("user_profiles", data, profile_fields, "user_id", user_id)
    if len(params_p) > 1:
        existing = execute_query_one("SELECT user_id FROM user_profiles WHERE user_id = %s", (user_id,))
        if existing:
            execute_update(sql_p, params_p)
        else:
            # 先插入再更新
            execute_insert(
                "INSERT INTO user_profiles (user_id, updated_at) VALUES (%s, NOW())", (user_id,)
            )
            execute_update(sql_p, params_p)

    if len(params_u) > 1 or len(params_p) > 1:
        log_operation(user_id, "PATCH_PROFILE", "user", user_id, "部分更新资料", _get_ip())

    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at "
        "FROM users WHERE id = %s", (user_id,)
    )
    profile = execute_query_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    return success({"user": _full_user(user, profile)})


# ── #4 GET /api/v1/users/<user_id>/public ──────────────
@users_bp.get("/<int:user_id>/public")
def get_public_profile(user_id):
    """获取指定用户的公开资料"""
    user = execute_query_one(
        "SELECT id, nickname, avatar_url, role FROM users WHERE id = %s AND deleted_at IS NULL",
        (user_id,),
    )
    if not user:
        return error("用户不存在", 404)

    profile = execute_query_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    return success({"user": _public_user(user, profile)})


# ── #5 GET /api/v1/users/<user_id>/stats ───────────────
@users_bp.get("/<int:user_id>/stats")
def get_user_stats(user_id):
    """获取用户统计数据"""
    user = execute_query_one("SELECT id, nickname, avatar_url FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
    if not user:
        return error("用户不存在", 404)

    stats = execute_query_one("SELECT * FROM user_stats WHERE user_id = %s", (user_id,))
    if not stats:
        stats = {"vitality": 0, "activity_count": 0, "activity_streak": 0, "friends_count": 0, "last_active_at": None}

    return success({
        "user": _safe_user(user),
        "stats": {
            "vitality": stats["vitality"],
            "activity_count": stats["activity_count"],
            "activity_streak": stats["activity_streak"],
            "friends_count": stats["friends_count"],
            "last_active_at": str(stats["last_active_at"]) if stats.get("last_active_at") else None,
        },
    })


# ── #6 GET /api/v1/users/search ────────────────────────
@users_bp.get("/search")
def search_users():
    """按昵称搜索用户，分页"""
    keyword = request.args.get("keyword", "").strip()
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    offset = (page - 1) * size

    if not keyword:
        return error("请输入搜索关键词", 400)

    like_pattern = f"%{keyword}%"
    total = execute_query_one(
        "SELECT COUNT(*) AS cnt FROM users WHERE nickname LIKE %s AND deleted_at IS NULL",
        (like_pattern,),
    )["cnt"]

    users = execute_query(
        "SELECT id, nickname, avatar_url, role FROM users "
        "WHERE nickname LIKE %s AND deleted_at IS NULL "
        "ORDER BY updated_at DESC LIMIT %s OFFSET %s",
        (like_pattern, size, offset),
    )

    return success({
        "items": [_safe_user(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
    })


# ── #7 POST /api/v1/users/upload-avatar ────────────────
@users_bp.post("/upload-avatar")
@require_auth
def upload_avatar():
    """上传头像（存 URL）"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    avatar_url = data.get("avatar_url", "")

    if not avatar_url:
        return error("请提供 avatar_url", 400)

    execute_update(
        "UPDATE users SET avatar_url = %s, updated_at = NOW() WHERE id = %s",
        (avatar_url, user_id),
    )

    log_operation(user_id, "UPLOAD_AVATAR", "user", user_id, f"更新头像", _get_ip())
    return success({"avatar_url": avatar_url}, "头像已更新")


# ═══════════════════════════════════════════════════════
# 好友管理
# ═══════════════════════════════════════════════════════

# ── #8 POST /api/v1/users/friends/request ──────────────
@users_bp.post("/friends/request")
@require_auth
def send_friend_request():
    """发送好友申请"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")
    message = data.get("message", "")

    if not target_user_id:
        return error("请指定目标用户", 400)
    if target_user_id == user_id:
        return error("不能添加自己为好友", 400)

    # 目标用户存在？
    target = execute_query_one(
        "SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (target_user_id,)
    )
    if not target:
        return error("用户不存在", 404)

    # 检查是否已存在好友关系
    existing = execute_query_one(
        "SELECT id, status FROM user_friends "
        "WHERE user_id = %s AND friend_id = %s AND deleted_at IS NULL",
        (user_id, target_user_id),
    )
    if existing:
        if existing["status"] == "active":
            return error("已是好友", 409)
        if existing["status"] == "pending":
            return error("已发送过好友申请", 409)

    execute_insert(
        "INSERT INTO user_friends (user_id, friend_id, source, status, created_at, updated_at) "
        "VALUES (%s, %s, 'activity', 'pending', NOW(), NOW())",
        (user_id, target_user_id),
    )

    log_operation(user_id, "FRIEND_REQUEST", "user_friends", target_user_id, message, _get_ip())
    return success(None, "好友申请已发送")


# ── #9 PUT /api/v1/users/friends/request/<request_id> ──
@users_bp.put("/friends/request/<int:request_id>")
@require_auth
def handle_friend_request(request_id):
    """处理好友申请"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action not in ("accept", "reject"):
        return error("action 必须为 accept 或 reject", 400)

    # 查找申请（当前用户是被请求方）
    req = execute_query_one(
        "SELECT id, user_id, friend_id FROM user_friends WHERE id = %s AND friend_id = %s AND status = 'pending' AND deleted_at IS NULL",
        (request_id, user_id),
    )
    if not req:
        return error("好友申请不存在或已处理", 404)

    if action == "accept":
        # 更新原申请为 active
        execute_update(
            "UPDATE user_friends SET status = 'active', updated_at = NOW() WHERE id = %s",
            (request_id,),
        )
        # 添加反向关系
        existing_reverse = execute_query_one(
            "SELECT id FROM user_friends WHERE user_id = %s AND friend_id = %s AND deleted_at IS NULL",
            (user_id, req["user_id"]),
        )
        if not existing_reverse:
            execute_insert(
                "INSERT INTO user_friends (user_id, friend_id, source, status, created_at, updated_at) "
                "VALUES (%s, %s, 'mutual', 'active', NOW(), NOW())",
                (user_id, req["user_id"]),
            )
        # 更新双方好友计数
        execute_update(
            "INSERT INTO user_stats (user_id, friends_count, updated_at) VALUES (%s, 1, NOW()) "
            "ON DUPLICATE KEY UPDATE friends_count = friends_count + 1, updated_at = NOW()",
            (user_id,),
        )
        execute_update(
            "INSERT INTO user_stats (user_id, friends_count, updated_at) VALUES (%s, 1, NOW()) "
            "ON DUPLICATE KEY UPDATE friends_count = friends_count + 1, updated_at = NOW()",
            (req["user_id"],),
        )
        msg = "已接受好友申请"
    else:
        execute_update(
            "UPDATE user_friends SET status = 'rejected', updated_at = NOW() WHERE id = %s",
            (request_id,),
        )
        msg = "已拒绝好友申请"

    log_operation(user_id, f"FRIEND_{action.upper()}", "user_friends", request_id, msg, _get_ip())
    return success(None, msg)


# ── #10 GET /api/v1/users/friends ──────────────────────
@users_bp.get("/friends")
@require_auth
def list_friends():
    """获取好友列表"""
    user_id = g.current_user["user_id"]
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    offset = (page - 1) * size

    total = execute_query_one(
        "SELECT COUNT(*) AS cnt FROM user_friends uf "
        "JOIN users u ON u.id = uf.friend_id "
        "WHERE uf.user_id = %s AND uf.status = 'active' AND uf.deleted_at IS NULL AND u.deleted_at IS NULL",
        (user_id,),
    )["cnt"]

    friends = execute_query(
        "SELECT uf.friend_id, u.nickname, u.avatar_url, uf.source, uf.created_at "
        "FROM user_friends uf "
        "JOIN users u ON u.id = uf.friend_id "
        "WHERE uf.user_id = %s AND uf.status = 'active' AND uf.deleted_at IS NULL AND u.deleted_at IS NULL "
        "ORDER BY uf.created_at DESC LIMIT %s OFFSET %s",
        (user_id, size, offset),
    )

    items = []
    for f in friends:
        items.append({
            "user_id": f["friend_id"],
            "nickname": f["nickname"],
            "avatar_url": f.get("avatar_url", ""),
            "source": f["source"],
            "created_at": str(f["created_at"]) if f.get("created_at") else None,
        })

    return success({"items": items, "total": total, "page": page, "size": size})


# ── #11 DELETE /api/v1/users/friends/<friend_id> ───────
@users_bp.delete("/friends/<int:friend_id>")
@require_auth
def remove_friend(friend_id):
    """删除好友（软删除，双向）"""
    user_id = g.current_user["user_id"]

    # 正向
    execute_update(
        "UPDATE user_friends SET status = 'deleted', deleted_at = NOW(), updated_at = NOW() "
        "WHERE user_id = %s AND friend_id = %s AND deleted_at IS NULL",
        (user_id, friend_id),
    )
    # 反向
    execute_update(
        "UPDATE user_friends SET status = 'deleted', deleted_at = NOW(), updated_at = NOW() "
        "WHERE user_id = %s AND friend_id = %s AND deleted_at IS NULL",
        (friend_id, user_id),
    )

    log_operation(user_id, "FRIEND_DELETE", "user_friends", friend_id, "删除好友", _get_ip())
    return success(None, "已删除好友")


# ═══════════════════════════════════════════════════════
# 私信
# ═══════════════════════════════════════════════════════

# ── #12 GET /api/v1/users/messages ─────────────────────
@users_bp.get("/messages")
@require_auth
def list_messages():
    """获取私信列表（按会话聚合，显示最新一条）"""
    user_id = g.current_user["user_id"]
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    offset = (page - 1) * size

    # 按会话聚合：每个对话对方的最新一条消息
    total = execute_query_one(
        "SELECT COUNT(DISTINCT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END) AS cnt "
        "FROM user_private_messages WHERE (sender_id = %s OR receiver_id = %s) AND deleted_at IS NULL",
        (user_id, user_id, user_id),
    )["cnt"]

    # 取每个会话的最新消息
    conversations = execute_query(
        "SELECT m.id, m.sender_id, m.receiver_id, m.msg_type, m.content, m.is_read, m.created_at "
        "FROM user_private_messages m "
        "INNER JOIN ("
        "  SELECT MAX(id) AS max_id FROM user_private_messages "
        "  WHERE (sender_id = %s OR receiver_id = %s) AND deleted_at IS NULL "
        "  GROUP BY CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END"
        ") latest ON m.id = latest.max_id "
        "ORDER BY m.created_at DESC LIMIT %s OFFSET %s",
        (user_id, user_id, user_id, size, offset),
    )

    items = []
    for msg in conversations:
        other_id = msg["receiver_id"] if msg["sender_id"] == user_id else msg["sender_id"]
        other = execute_query_one(
            "SELECT id, nickname, avatar_url FROM users WHERE id = %s", (other_id,)
        )
        items.append({
            "message_id": msg["id"],
            "other_user": _safe_user(other) if other else {"user_id": other_id},
            "msg_type": msg["msg_type"],
            "content": msg["content"],
            "is_read": bool(msg["is_read"]),
            "created_at": str(msg["created_at"]) if msg.get("created_at") else None,
        })

    return success({"items": items, "total": total, "page": page, "size": size})


# ── #13 POST /api/v1/users/messages ────────────────────
@users_bp.post("/messages")
@require_auth
def send_message():
    """发送私信"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    content = data.get("content", "")

    if not receiver_id:
        return error("请指定接收者", 400)
    if not content or len(content.strip()) == 0:
        return error("消息内容不能为空", 400)
    if receiver_id == user_id:
        return error("不能给自己发消息", 400)

    receiver = execute_query_one(
        "SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (receiver_id,)
    )
    if not receiver:
        return error("用户不存在", 404)

    msg_id = execute_insert(
        "INSERT INTO user_private_messages (sender_id, receiver_id, msg_type, content, created_at) "
        "VALUES (%s, %s, 'text', %s, NOW())",
        (user_id, receiver_id, content.strip()),
    )

    log_operation(user_id, "SEND_MESSAGE", "user_private_messages", msg_id, f"to={receiver_id}", _get_ip())
    return success({"message_id": msg_id}, "消息已发送")


# ── #14 POST /api/v1/users/<user_id>/report ────────────
@users_bp.post("/<int:target_id>/report")
@require_auth
def report_user(target_id):
    """举报用户"""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "")
    description = data.get("description", "")

    if not reason:
        return error("请选择举报原因", 400)
    if target_id == user_id:
        return error("不能举报自己", 400)

    target = execute_query_one(
        "SELECT id, nickname FROM users WHERE id = %s AND deleted_at IS NULL", (target_id,)
    )
    if not target:
        return error("用户不存在", 404)

    log_operation(
        operator_id=user_id,
        action="REPORT_USER",
        target_type="user",
        target_id=target_id,
        detail=f"举报原因: {reason}, 描述: {description}",
        ip_address=_get_ip(),
    )

    return success(None, "举报已提交")
