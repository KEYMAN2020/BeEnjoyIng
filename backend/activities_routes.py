"""活动模块路由 — 24 个 API 端点

路由前缀: /api/v1/activities
"""

import math
import json
import urllib.request
from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from jwt_helper import decode_token
from operation_log import log_operation
from config import Config

activities_bp = Blueprint("activities", __name__)


# ── 辅助函数 ─────────────────────────────────────────────


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


def _haversine(lat1, lng1, lat2, lng2):
    """计算两点间直线距离（米）"""
    if None in (lat1, lng1, lat2, lng2):
        return None
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def _try_get_current_user():
    """可选鉴权：尝试解析 JWT，不强制"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_token(auth_header[len("Bearer "):])
        if payload:
            return payload
    return None


def _activity_to_dict(a: dict) -> dict:
    """活动信息转字典"""
    status_map = {
        "open": {"text": "进行中", "color": "green"},
        "ended": {"text": "已结束", "color": "gray"},
        "disbanded": {"text": "已解散", "color": "red"},
        "expired": {"text": "已过期", "color": "orange"},
        "closed": {"text": "已结束", "color": "gray"},
    }
    from datetime import datetime
    st = a["status"]
    # Check if end_time has passed
    end_str = a.get("end_time")
    if end_str and st in ("approved", "open", "pending"):
        try:
            end_dt = end_str if isinstance(end_str, datetime) else datetime.fromisoformat(str(end_str).replace("Z","+00:00"))
            if end_dt < datetime.now(end_dt.tzinfo) if end_dt.tzinfo else end_dt < datetime.now():
                st = "ended"
        except: pass
    sinfo = status_map.get(st, {"text": st, "color": "gray"})

    return {
        "id": a["id"],
        "captain_id": a["captain_id"],
        "category_id": a["category_id"],
        "title": a["title"],
        "description": a.get("description", ""),
        "cover_image": a.get("cover_image", ""),
        "location_name": a["location_name"],
        "location_address": a.get("location_address", ""),
        "location_lat": a.get("location_lat"),
        "location_lng": a.get("location_lng"),
        "city": a.get("city", ""),
        "district": a.get("district", ""),
        "start_time": a["start_time"].isoformat() if hasattr(a["start_time"], "isoformat") else a["start_time"],
        "end_time": a["end_time"].isoformat() if hasattr(a["end_time"], "isoformat") else a["end_time"],
        "signup_deadline": a["signup_deadline"].isoformat() if a.get("signup_deadline") and hasattr(a["signup_deadline"], "isoformat") else a.get("signup_deadline"),
        "max_participants": a["max_participants"],
        "min_participants": a.get("min_participants", 1),
        "current_participants": a["current_participants"],
        "has_waitlist": bool(a["has_waitlist"]),
        "price": float(a["price"]),
        "safety_level": a["safety_level"],
        "age_min": a.get("age_min"),
        "age_max": a.get("age_max"),
        "status": a["status"],
        "status_text": sinfo["text"],
        "status_color": sinfo["color"],
        "captain": {
            "id": a["captain_id"],
            "nickname": a.get("captain_nickname", ""),
            "avatar_url": a.get("captain_avatar_url", ""),
            "phone": a.get("captain_phone", ""),
        } if a.get("captain_nickname") is not None else None,
        "is_captain": a.get("is_captain", 0) == 1,
        "reject_reason": a.get("reject_reason"),
        "created_at": a["created_at"].isoformat() if hasattr(a["created_at"], "isoformat") else a["created_at"],
    }


# ═══════════════════════════════════════════════════════
# 1. 活动列表
# ═══════════════════════════════════════════════════════
@activities_bp.get("")
def list_activities():
    """获取活动列表（支持筛选和分页）
    ---
    tags:
      - 活动
    parameters:
      - name: category_id
        in: query
        type: integer
        required: false
        description: 分类ID
      - name: city
        in: query
        type: string
        required: false
        description: 城市
      - name: status
        in: query
        type: string
        required: false
        default: approved
        description: 状态（默认只显示开启中）
      - name: start_date
        in: query
        type: string
        required: false
        description: 起始日期
      - name: end_date
        in: query
        type: string
        required: false
      - name: keyword
        in: query
        type: string
        required: false
        description: 标题关键词搜索
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: 活动列表（分页）
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                activities: {type: array}
                total: {type: integer}
                page: {type: integer}
                per_page: {type: integer}
    """
    category_id = request.args.get("category_id", type=int)
    city = request.args.get("city", "")
    status = request.args.get("status", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    keyword = request.args.get("keyword", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    conditions = ["a.deleted_at IS NULL"]
    params = []

    if category_id:
        conditions.append("a.category_id = %s")
        params.append(category_id)
    if city:
        conditions.append("a.city = %s")
        params.append(city)
    if status:
        conditions.append("a.status = %s")
        params.append(status)
    else:
        conditions.append("a.status = 'open'")  # 默认只看开启中
    if start_date:
        conditions.append("a.start_time >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("a.end_time <= %s")
        params.append(end_date)
    if keyword:
        conditions.append("a.title LIKE %s")
        params.append(f"%{keyword}%")

    where = " AND ".join(conditions)

    # 总数
    count_sql = f"SELECT COUNT(*) AS total FROM activities a WHERE {where}"
    total = execute_query_one(count_sql, params)["total"]

    offset = (page - 1) * per_page
    sql = f"""SELECT a.*,
                       u.nickname AS captain_nickname,
                       u.avatar_url AS captain_avatar_url,
                       u.phone AS captain_phone
                FROM activities a
                LEFT JOIN users u ON u.id = a.captain_id
              WHERE {where}
              ORDER BY CASE WHEN a.end_time > NOW() AND a.status NOT IN ('ended','closed','disbanded') THEN 0 ELSE 1 END, CASE WHEN a.end_time > NOW() THEN a.start_time END ASC, a.end_time DESC
              LIMIT %s OFFSET %s"""
    rows = execute_query(sql, params + [per_page, offset])

    return success({
        "activities": [_activity_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ═══════════════════════════════════════════════════════
# 2. 创建活动
# ═══════════════════════════════════════════════════════
@activities_bp.post("")
@require_auth
def create_activity():
    """创建活动（领队/合作伙伴）
    ---
    tags:
      - 活动

    # 请求: {title, description, cover_image, category_id, location_name, location_address,
    #        location_lat, location_lng, city, district, start_time, end_time,
    #        signup_deadline, max_participants, min_participants, current_participants, price, safety_level,
    #        age_min, age_max, has_waitlist, tags}
    """
    data = request.get_json(silent=True) or {}
    user_id = g.current_user["user_id"]

    # 每个人最多同时创建 3 个「开启中」的活动（只计算自己创建的，加入别人的不限制）
    active_count = execute_query_one(
        "SELECT COUNT(*) AS cnt FROM activities WHERE captain_id = %s AND status = 'open' AND deleted_at IS NULL",
        (user_id,),
    )
    if active_count and active_count["cnt"] >= 3:
        return error("您最多同时创建 3 个开启中的活动，请先结束或解散已有活动", 400)

    title = data.get("title", "")
    if not title or len(title) < 2:
        return error("活动标题至少 2 个字符", 400)

    category_id = data.get("category_id")
    if not category_id:
        return error("请选择活动分类", 400)

    required_fields = ["location_name", "start_time", "end_time", "max_participants"]
    for field in required_fields:
        if not data.get(field):
            return error(f"缺少必填字段: {field}", 400)

    activity_id = execute_insert(
        """INSERT INTO activities
           (captain_id, category_id, title, description, cover_image,
            location_name, location_address, location_lat, location_lng,
            city, district, start_time, end_time, signup_deadline,
            max_participants, min_participants, current_participants, price, safety_level,
            age_min, age_max, has_waitlist, status, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                   %s, %s, %s, %s, %s, %s, %s, %s, 'open', NOW(), NOW())""",
        (
            user_id, category_id, title, data.get("description", ""),
            data.get("cover_image", ""),
            data["location_name"], data.get("location_address", ""),
            data.get("location_lat"), data.get("location_lng"),
            data.get("city", ""), data.get("district", ""),
            data["start_time"], data["end_time"], data.get("signup_deadline"),
            data["max_participants"], data.get("min_participants", 1), 1,
            data.get("price", 0), data.get("safety_level", "green"),
            data.get("age_min"), data.get("age_max"),
            data.get("has_waitlist", 0),
        ),
    )

    # 添加标签
    tags = data.get("tags", [])
    if tags and isinstance(tags, list):
        for tag_id in tags:
            execute_insert(
                "INSERT INTO activity_tag_refs (activity_id, tag_id, created_at) VALUES (%s, %s, NOW())",
                (activity_id, tag_id),
            )

    # 创建者自动报名（计数 +1）
    execute_insert(
        "INSERT INTO activity_signups (activity_id, user_id, status, signed_up_at, created_at, updated_at) VALUES (%s, %s, 'registered', NOW(), NOW(), NOW())",
        (activity_id, user_id),
    )
    execute_update(
        "UPDATE activities SET current_participants = COALESCE(current_participants, 0) + 1 WHERE id = %s",
        (activity_id,),
    )

    # 自动创建活动群聊
    group_id = execute_insert(
        """INSERT INTO chat_groups
           (activity_id, name, captain_id, member_count, status, created_at, updated_at)
           VALUES (%s, %s, %s, 1, 'active', NOW(), NOW())""",
        (activity_id, title, user_id),
    )

    # 创建者自动加入群聊
    execute_insert(
        """INSERT INTO chat_group_members
           (group_id, user_id, joined_at, created_at)
           VALUES (%s, %s, NOW(), NOW())""",
        (group_id, user_id),
    )

    # 发送通知：已加入活动群聊
    execute_insert(
        """INSERT INTO notifications
           (user_id, type, title, content, ref_type, ref_id, created_at)
           VALUES (%s, 'system', %s, %s, 'activity', %s, NOW())""",
        (user_id, "已加入活动群聊", f"您已加入「{title}」活动群聊", activity_id),
    )

    log_operation(
        operator_id=user_id,
        action="CREATE_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"创建活动: {title}",
        ip_address=_get_ip(),
    )

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s", (activity_id,)
    )
    return success(_activity_to_dict(activity), "活动已创建"), 201


# ═══════════════════════════════════════════════════════
# 3. 活动分类列表
# ═══════════════════════════════════════════════════════
@activities_bp.get("/categories")
def list_categories():
    """获取活动分类列表
    ---
    tags:
      - 活动
    """
    rows = execute_query(
        "SELECT * FROM activity_categories WHERE is_active = 1 AND deleted_at IS NULL ORDER BY sort_order ASC",
    )
    return success({
        "categories": [{
            "id": r["id"],
            "name": r["name"],
            "icon": r.get("icon", ""),
            "color": r.get("color", "#666666"),
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 4. 活动标签列表
# ═══════════════════════════════════════════════════════
@activities_bp.get("/tags")
def list_tags():
    """获取活动标签列表
    ---
    tags:
      - 活动
    """
    rows = execute_query(
        "SELECT * FROM activity_tags WHERE is_active = 1 ORDER BY sort_order ASC",
    )
    return success({
        "tags": [{
            "id": r["id"],
            "name": r["name"],
            "icon": r.get("icon", ""),
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 5. 我的活动
# ═══════════════════════════════════════════════════════
@activities_bp.get("/my")
@require_auth
def my_activities():
    """获取我的活动列表（我报名参与的 + 我创建的）
    ---
    tags:
      - 活动

    查询参数: type (participant/captain/all), status, page, per_page
    """
    user_id = g.current_user["user_id"]
    act_type = request.args.get("type", "all")
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    if act_type == "captain":
        conditions = ["a.captain_id = %s", "a.deleted_at IS NULL"]
        params = [user_id]
        if status:
            conditions.append("a.status = %s")
            params.append(status)
        where = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) AS total FROM activities a WHERE {where}"
        total = execute_query_one(count_sql, params)["total"]

        offset = (page - 1) * per_page
        sql = f"""SELECT a.*, u.nickname AS captain_nickname,
                       u.avatar_url AS captain_avatar_url,
                       u.phone AS captain_phone,
                       CASE WHEN a.captain_id = %s THEN 1 ELSE 0 END AS is_captain
                  FROM activities a
                  LEFT JOIN users u ON u.id = a.captain_id
                  WHERE {where}
                  ORDER BY a.created_at DESC
                  LIMIT %s OFFSET %s"""
        rows = execute_query(sql, params + [user_id, per_page, offset])
    elif act_type == "participant":
        conditions = ["s.user_id = %s", "s.deleted_at IS NULL", "a.deleted_at IS NULL", "s.status != 'cancelled'"]
        params = [user_id]
        if status:
            if status in ("registered", "cancelled"):
                conditions.append("s.status = %s")
                params.append(status)
        where = " AND ".join(conditions)

        count_sql = f"""SELECT COUNT(*) AS total
                        FROM activity_signups s
                        JOIN activities a ON a.id = s.activity_id
                        WHERE {where}"""
        total = execute_query_one(count_sql, params)["total"]

        offset = (page - 1) * per_page
        sql = f"""SELECT a.*, u.nickname AS captain_nickname,
                       u.avatar_url AS captain_avatar_url,
                       u.phone AS captain_phone,
                       s.status AS signup_status, s.signed_up_at,
                       CASE WHEN a.captain_id = %s THEN 1 ELSE 0 END AS is_captain
                  FROM activity_signups s
                  JOIN activities a ON a.id = s.activity_id
                  LEFT JOIN users u ON u.id = a.captain_id
                  WHERE {where}
                  ORDER BY CASE WHEN a.end_time > NOW() AND a.status NOT IN ('ended','closed','disbanded') THEN 0 ELSE 1 END, CASE WHEN a.end_time > NOW() THEN a.start_time END ASC, a.end_time DESC
                  LIMIT %s OFFSET %s"""
        rows = execute_query(sql, params + [user_id, per_page, offset])
    else:
        # type=all: 我创建的 + 我报名的（去重）
        params = [user_id, user_id, per_page, (page - 1) * per_page]
        count_sql = """SELECT COUNT(*) AS total FROM (
            SELECT a.id FROM activities a WHERE a.captain_id = %s AND a.deleted_at IS NULL
            UNION
            SELECT a.id FROM activity_signups s
            JOIN activities a ON a.id = s.activity_id
            WHERE s.user_id = %s AND s.deleted_at IS NULL AND a.deleted_at IS NULL AND s.status != 'cancelled'
        ) AS t"""
        total = execute_query_one(count_sql, params[:2])["total"]

        sql = f"""SELECT a.*, u.nickname AS captain_nickname,
                           u.avatar_url AS captain_avatar_url,
                           u.phone AS captain_phone,
                           CASE WHEN a.captain_id = %s THEN 1 ELSE 0 END AS is_captain,
                        (SELECT s.status FROM activity_signups s
                         WHERE s.activity_id = a.id AND s.user_id = %s AND s.deleted_at IS NULL ORDER BY s.id DESC LIMIT 1) AS signup_status
                 FROM (
                     SELECT a.id FROM activities a WHERE a.captain_id = %s AND a.deleted_at IS NULL
                     UNION
                     SELECT a.id FROM activity_signups s
                     JOIN activities a ON a.id = s.activity_id
                     WHERE s.user_id = %s AND s.deleted_at IS NULL AND a.deleted_at IS NULL AND s.status != 'cancelled'
                 ) AS t
                 JOIN activities a ON a.id = t.id
                  LEFT JOIN users u ON u.id = a.captain_id
                 ORDER BY CASE WHEN a.end_time > NOW() AND a.status NOT IN ('ended','closed','disbanded') THEN 0 ELSE 1 END, CASE WHEN a.end_time > NOW() THEN a.start_time END ASC, a.end_time DESC
                 LIMIT %s OFFSET %s"""
        rows = execute_query(sql, [user_id, user_id, user_id, user_id, per_page, (page - 1) * per_page])

    return success({
        "activities": [_activity_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ═══════════════════════════════════════════════════════
# 6. 附近活动
# ═══════════════════════════════════════════════════════
@activities_bp.get("/nearby")
def nearby_activities():
    """获取附近活动
    ---
    tags:
      - 活动

    查询参数: lat, lng, radius_km (默认 10), page, per_page
    """
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius_km = request.args.get("radius_km", 10, type=float)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    if not lat or not lng:
        return error("需要提供经纬度", 400)

    # 使用简化的距离估算（1度 ≈ 111km）
    # 实际生产应使用 MySQL GIS 或 GeoHash
    lat_range = radius_km / 111.0
    lng_range = radius_km / (111.0 * 0.766)  # cos(40°)

    conditions = [
        "a.deleted_at IS NULL",
        "a.status = 'open'",
        "a.location_lat BETWEEN %s AND %s",
        "a.location_lng BETWEEN %s AND %s",
    ]
    params = [lat - lat_range, lat + lat_range, lng - lng_range, lng + lng_range]

    where = " AND ".join(conditions)

    count_sql = f"SELECT COUNT(*) AS total FROM activities a WHERE {where}"
    total = execute_query_one(count_sql, params)["total"]

    offset = (page - 1) * per_page
    sql = f"""SELECT a.* FROM activities a
              WHERE {where}
              ORDER BY CASE WHEN a.end_time > NOW() AND a.status NOT IN ('ended','closed','disbanded') THEN 0 ELSE 1 END, CASE WHEN a.end_time > NOW() THEN a.start_time END ASC, a.end_time DESC
              LIMIT %s OFFSET %s"""
    rows = execute_query(sql, params + [per_page, offset])

    return success({
        "activities": [_activity_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ═══════════════════════════════════════════════════════
# 7. 活动详情
# ═══════════════════════════════════════════════════════
@activities_bp.get("/<int:activity_id>")
def get_activity(activity_id):
    """获取活动详情（含可选用户上下文：my_status / is_favorited / 距离）
    ---
    tags:
      - 活动
    """
    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    result = _activity_to_dict(activity)
    # 活动日期从 start_time 提取（数据库无 activity_date 字段）
    st = activity.get("start_time")
    result["activity_date"] = st.isoformat()[:10] if hasattr(st, "isoformat") else (str(st)[:10] if st else "")

    # 获取标签
    tags = execute_query(
        """SELECT t.id, t.name, t.icon
           FROM activity_tag_refs tr
           JOIN activity_tags t ON t.id = tr.tag_id
           WHERE tr.activity_id = %s""",
        (activity_id,),
    )
    result["tags"] = [{"id": t["id"], "name": t["name"], "icon": t.get("icon", "")} for t in tags]

    # 获取领队信息（含手机号）
    captain = execute_query_one(
        "SELECT id, nickname, avatar_url, phone FROM users WHERE id = %s",
        (activity["captain_id"],),
    )
    if captain:
        result["captain"] = {
            "user_id": captain["id"],
            "nickname": captain["nickname"],
            "avatar_url": captain.get("avatar_url", ""),
            "phone": captain.get("phone", ""),
        }

    # 获取封面相册
    photos = execute_query(
        "SELECT image_url, description FROM activity_albums WHERE activity_id = %s AND deleted_at IS NULL ORDER BY sort_order ASC LIMIT 5",
        (activity_id,),
    )
    result["photos"] = [p["image_url"] for p in photos]

    # —— 可选用户上下文：my_status / is_favorited / 距离 ——
    user = _try_get_current_user()
    if user:
        user_id = user["user_id"]

        # 报名状态
        signup = execute_query_one(
            "SELECT status FROM activity_signups WHERE activity_id = %s AND user_id = %s AND deleted_at IS NULL",
            (activity_id, user_id),
        )
        result["my_status"] = signup["status"] if signup else None

        # 收藏状态
        fav = execute_query_one(
            "SELECT id FROM activity_favorites WHERE user_id = %s AND activity_id = %s",
            (user_id, activity_id),
        )
        result["is_favorited"] = bool(fav)
        result["is_captain"] = (user_id == activity["captain_id"])
        result["signup_status"] = signup["status"] if signup else None
    else:
        result["my_status"] = None
        result["is_favorited"] = False
        result["is_captain"] = False
        result["signup_status"] = None

    # 距离计算（请求传 lat / lng）
    try:
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
    except (TypeError, ValueError):
        lat = lng = None
    if lat and lng and activity.get("location_lat") and activity.get("location_lng"):
        result["distance"] = _haversine(
            lat, lng,
            float(activity["location_lat"]),
            float(activity["location_lng"]),
        )
    else:
        result["distance"] = None

    return success({"activity": result})


# ═══════════════════════════════════════════════════════
# 7a. 地点搜索（高德 Input Tips API）
# ═══════════════════════════════════════════════════════
@activities_bp.get("/search-places")
def search_places():
    """高德地图地点搜索提示
    ---
    tags:
      - 活动
    parameters:
      - name: keyword
        in: query
        type: string
        required: true
      - name: city
        in: query
        type: string
        required: false
    """
    keyword = request.args.get("keyword", "")
    city = request.args.get("city", "")
    if not keyword or len(keyword) < 1:
        return success({"places": []})

    import requests as req
    try:
        params = {
            "key": Config.AMAP_KEY,
            "keywords": keyword,
            "datatype": "all",
            "city": city or "",
        }
        r = req.get("https://restapi.amap.com/v3/assistant/inputtips", params=params, timeout=5)
        data = r.json()
        if data.get("status") == "1" and data.get("tips"):
            places = []
            for tip in data["tips"]:
                places.append({
                    "location_name": tip.get("name", ""),
                    "location_address": tip.get("address", ""),
                    "city": tip.get("city", ""),
                    "district": tip.get("district", ""),
                    "location": tip.get("location", ""),
                })
            return success({"places": places})
        return success({"places": []})
    except Exception as e:
        print(f"[Amap Input Tips] error: {e}")
        return success({"places": []})


# ═══════════════════════════════════════════════════════
# 7b. 活动天气（从高德天气 API 获取）
# ═══════════════════════════════════════════════════════
@activities_bp.get("/<int:activity_id>/weather")
def activity_weather(activity_id):
    """获取活动当天的天气预报
    ---
    tags:
      - 活动
    """
    activity = execute_query_one(
        "SELECT city, district, start_time FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    # 活动日期从 start_time 提取
    st = activity.get("start_time")
    activity_date = st.isoformat()[:10] if hasattr(st, "isoformat") else (str(st)[:10] if st else "")

    # 用城市名查 adcode
    city_name = activity.get("city", "").replace("市", "").replace("地区", "").replace("盟", "")
    adcode = None
    if city_name:
        row = execute_query_one(
            "SELECT code FROM regions WHERE (name LIKE %s OR name LIKE %s) AND level IN (1,2) LIMIT 1",
            (f"{city_name}%", f"{city_name}市%"),
        )
        if row:
            adcode = row["code"]

    if not adcode:
        return success({"weather": None, "message": "无法确定城市"})

    key = Config.AMAP_KEY
    if not key:
        return success({"weather": None, "message": "天气服务未配置"})

    url = (
        f"https://restapi.amap.com/v3/weather/weatherInfo"
        f"?key={key}&city={adcode}&extensions=all"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BeEnjoyIng/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Gaode Weather API] error: {e}")
        return success({"weather": None, "message": "获取天气失败"})

    if data.get("status") != "1" or not data.get("forecasts"):
        return success({"weather": None, "message": "天气数据为空"})
    casts = data["forecasts"][0].get("casts", [])
    matched = None
    for cast in casts:
        if cast.get("date") == activity_date:
            matched = {
                "date": cast["date"],
                "day_weather": cast.get("dayweather", ""),
                "night_weather": cast.get("nightweather", ""),
                "day_temp": cast.get("daytemp", ""),
                "night_temp": cast.get("nighttemp", ""),
                "day_wind": cast.get("daywind", ""),
            }
            break

    if not matched and casts:
        # 取最近一天的预报
        c = casts[0]
        matched = {
            "date": c.get("date", ""),
            "day_weather": c.get("dayweather", ""),
            "night_weather": c.get("nightweather", ""),
            "day_temp": c.get("daytemp", ""),
            "night_temp": c.get("nighttemp", ""),
            "day_wind": c.get("daywind", ""),
        }

    return success({"weather": matched})


# ═══════════════════════════════════════════════════════
# 8. 更新活动
# ═══════════════════════════════════════════════════════
@activities_bp.put("/<int:activity_id>")
@require_auth
def update_activity(activity_id):
    """更新活动信息（仅创建者可操作）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id and g.current_user.get("role") != "admin":
        return error("无权修改此活动", 403)
    if activity["status"] != "open" and g.current_user.get("role") != "admin":
        return error("仅开启中的活动可以修改", 400)

    data = request.get_json(silent=True) or {}
    updates = []
    params = []

    updatable_fields = [
        "title", "description", "cover_image", "category_id",
        "location_name", "location_address", "location_lat", "location_lng",
        "city", "district", "start_time", "end_time", "signup_deadline",
        "max_participants", "min_participants", "price", "safety_level",
        "age_min", "age_max", "has_waitlist",
    ]
    for field in updatable_fields:
        if field in data:
            updates.append(f"{field} = %s")
            params.append(data[field])

    if not updates:
        return error("没有需要更新的字段", 400)

    updates.append("updated_at = NOW()")
    params.append(activity_id)

    sql = f"UPDATE activities SET {', '.join(updates)} WHERE id = %s"
    execute_update(sql, params)

    # 更新标签
    if "tags" in data and isinstance(data["tags"], list):
        execute_update(
            "DELETE FROM activity_tag_refs WHERE activity_id = %s",
            (activity_id,),
        )
        for tag_id in data["tags"]:
            execute_insert(
                "INSERT INTO activity_tag_refs (activity_id, tag_id, created_at) VALUES (%s, %s, NOW())",
                (activity_id, tag_id),
            )

    log_operation(
        operator_id=user_id,
        action="UPDATE_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"更新活动: {activity['title']}",
        ip_address=_get_ip(),
    )

    updated = execute_query_one(
        "SELECT * FROM activities WHERE id = %s", (activity_id,)
    )
    return success({"activity": _activity_to_dict(updated)}, "活动已更新")


# ═══════════════════════════════════════════════════════
# 9. 删除活动
# ═══════════════════════════════════════════════════════
@activities_bp.delete("/<int:activity_id>")
@require_auth
def delete_activity(activity_id):
    """删除活动（软删除，仅创建者或管理员）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]
    role = g.current_user.get("role", "user")

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id and role != "admin":
        return error("无权删除此活动", 403)

    execute_update(
        "UPDATE activities SET deleted_at = NOW(), updated_at = NOW() WHERE id = %s",
        (activity_id,),
    )

    log_operation(
        operator_id=user_id,
        action="DELETE_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"删除活动: {activity['title']}",
        ip_address=_get_ip(),
    )

    return success(None, "活动已删除")


# ═══════════════════════════════════════════════════════
# 9b. 解散活动（创建者手动解散）
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/disband")
@require_auth
def disband_activity(activity_id):
    """解散活动（仅创建者）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id:
        return error("仅活动创建者可以解散活动", 403)

    if activity["status"] != "open":
        return error("仅开启中的活动可以解散", 400)

    execute_update(
        "UPDATE activities SET status = 'disbanded', updated_at = NOW() WHERE id = %s",
        (activity_id,),
    )

    # 发送通知给创建者
    try:
        execute_insert(
            "INSERT INTO notifications (user_id, title, content, type, ref_type, ref_id, created_at) VALUES (%s, %s, %s, 'system', 'activity', %s, NOW())",
            (user_id, "活动已解散", f"您已成功解散活动「{activity['title']}」", activity_id),
        )
    except Exception:
        pass

    log_operation(
        operator_id=user_id,
        action="DISBAND_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"解散活动: {activity['title']}",
        ip_address=_get_ip(),
    )

    # 自动解散群聊
    try:
        execute_update(
            "UPDATE chat_groups SET status = 'disbanded', updated_at = NOW() WHERE activity_id = %s AND status = 'active'",
            (activity_id,),
        )
    except Exception:
        pass

    return success(None, "活动已解散")


# ═══════════════════════════════════════════════════════
# 9c. 完成活动（创建者标记活动为已结束）
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/complete")
@require_auth
def complete_activity(activity_id):
    """完成/结束活动（仅创建者）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id:
        return error("仅活动创建者可以结束活动", 403)
    if activity["status"] != "open":
        return error("仅开启中的活动可以结束", 400)

    execute_update(
        "UPDATE activities SET status = 'ended', updated_at = NOW() WHERE id = %s",
        (activity_id,),
    )

    # 通知创建者
    try:
        execute_insert(
            "INSERT INTO notifications (user_id, title, content, type, ref_type, ref_id, created_at) VALUES (%s, %s, %s, 'system', 'activity', %s, NOW())",
            (user_id, "活动已结束", f"活动「{activity['title']}」已顺利完成", activity_id),
        )
    except Exception:
        pass

    log_operation(
        operator_id=user_id,
        action="COMPLETE_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"完成活动: {activity['title']}",
        ip_address=_get_ip(),
    )

    return success(None, "活动已结束")


def _auto_close_expired_activities():
    """自动将超过结束时间 3 天的开启中活动标记为已过期"""
    try:
        execute_update("""
            UPDATE activities
            SET status = 'expired', updated_at = NOW()
            WHERE status = 'open'
              AND end_time IS NOT NULL
              AND end_time < DATE_SUB(NOW(), INTERVAL 3 DAY)
              AND deleted_at IS NULL
        """)
        # 通知创建者
        rows = execute_query("""
            SELECT id, captain_id, title FROM activities
            WHERE status = 'expired'
              AND updated_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
              AND deleted_at IS NULL
        """)
        for r in (rows or []):
            try:
                execute_insert(
                    "INSERT INTO notifications (user_id, title, content, type, ref_type, ref_id, created_at) VALUES (%s, %s, %s, 'system', 'activity', %s, NOW())",
                    (r["captain_id"], "活动已过期", f"活动「{r['title']}」已结束超过3天，系统已自动标记为已过期", r["id"]),
                )
            except Exception:
                pass
    except Exception as e:
        print(f"[AutoExpire] error: {e}")


# ═══════════════════════════════════════════════════════
# 10. 报名活动
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/signup")
@require_auth
def signup_activity(activity_id):
    """报名参加活动
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["status"] != "open":
        return error("活动当前不可报名", 400)

    # 检查是否已报名
    existing = execute_query_one(
        "SELECT id, status FROM activity_signups WHERE activity_id = %s AND user_id = %s AND deleted_at IS NULL",
        (activity_id, user_id),
    )
    if existing:
        if existing["status"] == "registered":
            return error("您已报名该活动", 409)
        if existing["status"] == "cancelled":
            # 重新报名
            execute_update(
                "UPDATE activity_signups SET status = 'registered', signed_up_at = NOW(), updated_at = NOW() WHERE id = %s",
                (existing["id"],),
            )
            execute_update(
                "UPDATE activities SET current_participants = current_participants + 1 WHERE id = %s",
                (activity_id,),
            )
            log_operation(
                operator_id=user_id,
                action="RESIGNUP_ACTIVITY",
                target_type="activity",
                target_id=activity_id,
                ip_address=_get_ip(),
            )
            # 重新加入群聊
            try:
                group = execute_query_one(
                    "SELECT id FROM chat_groups WHERE activity_id = %s AND status = 'active' LIMIT 1",
                    (activity_id,),
                )
                if group:
                    already_in = execute_query_one(
                        "SELECT id FROM chat_group_members WHERE group_id = %s AND user_id = %s",
                        (group["id"], user_id),
                    )
                    if not already_in:
                        execute_insert(
                            "INSERT INTO chat_group_members (group_id, user_id, joined_at, created_at) VALUES (%s, %s, NOW(), NOW())",
                            (group["id"], user_id),
                        )
            except Exception:
                pass
            return success(None, "已重新报名")

    if activity["current_participants"] >= activity["max_participants"]:
        return error("活动名额已满", 400)

    signup_id = execute_insert(
        """INSERT INTO activity_signups
           (activity_id, user_id, status, signed_up_at, created_at, updated_at)
           VALUES (%s, %s, 'registered', NOW(), NOW(), NOW())""",
        (activity_id, user_id),
    )

    execute_update(
        "UPDATE activities SET current_participants = current_participants + 1 WHERE id = %s",
        (activity_id,),
    )

    log_operation(
        operator_id=user_id,
        action="SIGNUP_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        ip_address=_get_ip(),
    )

    # 自动加入活动群聊
    try:
        group = execute_query_one(
            "SELECT id FROM chat_groups WHERE activity_id = %s AND status = 'active' LIMIT 1",
            (activity_id,),
        )
        if group:
            already_in = execute_query_one(
                "SELECT id FROM chat_group_members WHERE group_id = %s AND user_id = %s",
                (group["id"], user_id),
            )
            if not already_in:
                execute_insert(
                    "INSERT INTO chat_group_members (group_id, user_id, joined_at, created_at) VALUES (%s, %s, NOW(), NOW())",
                    (group["id"], user_id),
                )
                execute_update(
                    "UPDATE chat_groups SET member_count = member_count + 1, updated_at = NOW() WHERE id = %s",
                    (group["id"],),
                )
                # 发送入群通知
                try:
                    execute_insert(
                        "INSERT INTO notifications (user_id, type, title, content, ref_type, ref_id, created_at) VALUES (%s, 'system', %s, %s, 'activity', %s, NOW())",
                        (user_id, "已加入活动群聊", f"您已加入「{activity['title']}」活动群聊", activity_id),
                    )
                except Exception:
                    pass
    except Exception:
        pass

    return success({"signup_id": signup_id, "activity_id": activity_id}, "报名成功"), 201


# ═══════════════════════════════════════════════════════
# 11. 取消报名
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/cancel")
@require_auth
def cancel_signup(activity_id):
    """取消报名
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    signup = execute_query_one(
        "SELECT id FROM activity_signups WHERE activity_id = %s AND user_id = %s AND status = 'registered' AND deleted_at IS NULL",
        (activity_id, user_id),
    )
    if not signup:
        return error("未找到报名记录", 404)

    execute_update(
        "UPDATE activity_signups SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW() WHERE id = %s",
        (signup["id"],),
    )

    execute_update(
        "UPDATE activities SET current_participants = GREATEST(current_participants - 1, 0) WHERE id = %s",
        (activity_id,),
    )

    # 检查是否有候补
    activity = execute_query_one(
        "SELECT has_waitlist FROM activities WHERE id = %s", (activity_id,)
    )
    if activity and activity["has_waitlist"]:
        next_wait = execute_query_one(
            "SELECT id, user_id FROM activity_waitlist WHERE activity_id = %s AND status = 'waiting' ORDER BY queue_order ASC LIMIT 1",
            (activity_id,),
        )
        if next_wait:
            execute_update(
                "UPDATE activity_waitlist SET status = 'promoted', promoted_at = NOW() WHERE id = %s",
                (next_wait["id"],),
            )

    log_operation(
        operator_id=user_id,
        action="CANCEL_SIGNUP",
        target_type="activity",
        target_id=activity_id,
        ip_address=_get_ip(),
    )

    return success(None, "已取消报名")


# ═══════════════════════════════════════════════════════
# 12. 报名列表（领队查看）
# ═══════════════════════════════════════════════════════
@activities_bp.get("/<int:activity_id>/signups")
@require_auth
def list_signups(activity_id):
    """获取活动报名列表（仅领队和管理员）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]
    role = g.current_user.get("role", "user")

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id and role != "admin":
        return error("无权查看报名列表", 403)

    rows = execute_query(
        """SELECT s.id, s.user_id, s.status, s.signed_up_at, s.cancelled_at,
                  u.nickname, u.avatar_url
           FROM activity_signups s
           JOIN users u ON u.id = s.user_id
           WHERE s.activity_id = %s AND s.deleted_at IS NULL
           ORDER BY s.signed_up_at ASC""",
        (activity_id,),
    )

    return success({
        "signups": [{
            "id": r["id"],
            "user_id": r["user_id"],
            "nickname": r["nickname"],
            "avatar_url": r.get("avatar_url", ""),
            "status": r["status"],
            "signed_up_at": r["signed_up_at"].isoformat() if hasattr(r["signed_up_at"], "isoformat") else r["signed_up_at"],
            "cancelled_at": r["cancelled_at"].isoformat() if r.get("cancelled_at") and hasattr(r["cancelled_at"], "isoformat") else r.get("cancelled_at"),
        } for r in rows],
        "total": len(rows),
    })


# ═══════════════════════════════════════════════════════
# 13. 签到
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/checkin")
@require_auth
def checkin_activity(activity_id):
    """活动签到（领队操作）
    ---
    tags:
      - 活动

    # 请求: {user_id}
    """
    captain_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != captain_id:
        return error("仅领队可以操作签到", 403)

    data = request.get_json(silent=True) or {}
    target_user_id = data.get("user_id")
    if not target_user_id:
        return error("缺少 user_id", 400)

    # 检查是否已签到
    existing = execute_query_one(
        "SELECT id FROM activity_checkins WHERE activity_id = %s AND user_id = %s",
        (activity_id, target_user_id),
    )
    if existing:
        return error("该用户已签到", 409)

    execute_insert(
        """INSERT INTO activity_checkins
           (activity_id, user_id, method, checked_in_by, checked_in_at, created_at)
           VALUES (%s, %s, 'manual', %s, NOW(), NOW())""",
        (activity_id, target_user_id, captain_id),
    )

    log_operation(
        operator_id=captain_id,
        action="CHECKIN",
        target_type="activity",
        target_id=activity_id,
        detail=f"签到 user_id={target_user_id}",
        ip_address=_get_ip(),
    )

    return success(None, "签到成功")


# ═══════════════════════════════════════════════════════
# 14. 收藏活动
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/favorite")
@require_auth
def favorite_activity(activity_id):
    """收藏活动
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT id FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    existing = execute_query_one(
        "SELECT id FROM activity_favorites WHERE user_id = %s AND activity_id = %s",
        (user_id, activity_id),
    )
    if existing:
        return error("已收藏", 409)

    execute_insert(
        "INSERT INTO activity_favorites (user_id, activity_id, created_at) VALUES (%s, %s, NOW())",
        (user_id, activity_id),
    )

    return success(None, "已收藏")


# ═══════════════════════════════════════════════════════
# 15. 取消收藏
# ═══════════════════════════════════════════════════════
@activities_bp.delete("/<int:activity_id>/favorite")
@require_auth
def unfavorite_activity(activity_id):
    """取消收藏活动
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    execute_update(
        "DELETE FROM activity_favorites WHERE user_id = %s AND activity_id = %s",
        (user_id, activity_id),
    )

    return success(None, "已取消收藏")


# ═══════════════════════════════════════════════════════
# 16. 评价活动
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/rate")
@require_auth
def rate_activity(activity_id):
    """评价活动
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    rating = data.get("rating", "")

    valid_ratings = ("好评", "中评", "差评")
    if rating not in valid_ratings:
        return error(f"评价等级必须为: {', '.join(valid_ratings)}", 400)

    # 检查是否报名并已参加
    signup = execute_query_one(
        "SELECT id FROM activity_signups WHERE activity_id = %s AND user_id = %s AND status = 'registered' AND deleted_at IS NULL",
        (activity_id, user_id),
    )
    if not signup:
        return error("您未参加此活动，无法评价", 400)

    existing = execute_query_one(
        "SELECT id FROM activity_ratings WHERE activity_id = %s AND user_id = %s",
        (activity_id, user_id),
    )
    if existing:
        return error("您已评价过此活动", 409)

    execute_insert(
        "INSERT INTO activity_ratings (activity_id, user_id, rating, created_at) VALUES (%s, %s, %s, NOW())",
        (activity_id, user_id, rating),
    )

    log_operation(
        operator_id=user_id,
        action="RATE_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"评价: {rating}",
        ip_address=_get_ip(),
    )

    return success(None, "评价成功"), 201


# ═══════════════════════════════════════════════════════
# 17. 活动审核（管理员）
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/review")
@require_auth
def review_activity(activity_id):
    """审核活动（管理员/运营）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]
    role = g.current_user.get("role", "user")
    if role != "admin":
        return error("仅管理员可以审核活动", 403)

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    if action not in ("approve", "reject"):
        return error("审核操作必须为 approve 或 reject", 400)

    new_status = "open" if action == "approve" else "rejected"
    execute_update(
        "UPDATE activities SET status = %s, updated_at = NOW() WHERE id = %s",
        (new_status, activity_id),
    )

    if action == "reject":
        reject_reason = data.get("comment", "")
        execute_update(
            "UPDATE activities SET reject_reason = %s WHERE id = %s",
            (reject_reason, activity_id),
        )

    execute_insert(
        """INSERT INTO activity_reviews
           (activity_id, reviewer_id, review_action, review_comment,
            safety_check_passed, reviewed_at, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
        (
            activity_id, user_id, action,
            data.get("comment", ""),
            data.get("safety_check_passed", False),
        ),
    )

    log_operation(
        operator_id=user_id,
        action=f"REVIEW_{action.upper()}",
        target_type="activity",
        target_id=activity_id,
        detail=f"{'通过' if action == 'approve' else '驳回'}活动: {activity['title']}",
        ip_address=_get_ip(),
    )

    return success(None, f"活动已{'通过' if action == 'approve' else '驳回'}")


# ═══════════════════════════════════════════════════════
# 18. 举报活动
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/report")
@require_auth
def report_activity(activity_id):
    """举报活动
    ---
    tags:
      - 活动

    # 请求: {reason: "..."}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "")
    if not reason:
        return error("请填写举报原因", 400)

    activity = execute_query_one(
        "SELECT id FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    log_operation(
        operator_id=user_id,
        action="REPORT_ACTIVITY",
        target_type="activity",
        target_id=activity_id,
        detail=f"举报活动: {reason}",
        ip_address=_get_ip(),
    )

    return success(None, "举报已提交")


# ═══════════════════════════════════════════════════════
# 19. 候补列表
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/waitlist")
@require_auth
def join_waitlist(activity_id):
    """加入候补名单
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if not activity["has_waitlist"]:
        return error("该活动未启用候补功能", 400)

    # 检查是否已在候补
    existing = execute_query_one(
        "SELECT id FROM activity_waitlist WHERE activity_id = %s AND user_id = %s AND status = 'waiting'",
        (activity_id, user_id),
    )
    if existing:
        return error("您已在候补名单中", 409)

    # 获取当前最大序号
    max_order = execute_query_one(
        "SELECT MAX(queue_order) AS max_order FROM activity_waitlist WHERE activity_id = %s",
        (activity_id,),
    )
    next_order = (max_order["max_order"] or 0) + 1

    execute_insert(
        """INSERT INTO activity_waitlist
           (activity_id, user_id, queue_order, status, created_at, updated_at)
           VALUES (%s, %s, %s, 'waiting', NOW(), NOW())""",
        (activity_id, user_id, next_order),
    )

    return success({"queue_position": next_order}, "已加入候补名单"), 201


# ═══════════════════════════════════════════════════════
# 20. 获取活动相册
# ═══════════════════════════════════════════════════════
@activities_bp.get("/<int:activity_id>/albums")
def list_albums(activity_id):
    """获取活动相册
    ---
    tags:
      - 活动
    """
    rows = execute_query(
        "SELECT * FROM activity_albums WHERE activity_id = %s AND deleted_at IS NULL ORDER BY sort_order ASC",
        (activity_id,),
    )
    return success({
        "photos": [{
            "id": r["id"],
            "image_url": r["image_url"],
            "description": r.get("description", ""),
            "sort_order": r["sort_order"],
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 21. 添加相册照片
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/albums")
@require_auth
def add_album_photo(activity_id):
    """添加活动相册照片（领队或管理员）
    ---
    tags:
      - 活动

    # 请求: {image_url, description?}
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id and g.current_user.get("role") != "admin":
        return error("仅领队可以添加相册照片", 403)

    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "")
    if not image_url:
        return error("请提供图片地址", 400)

    # 获取当前最大排序
    max_sort = execute_query_one(
        "SELECT MAX(sort_order) AS max_sort FROM activity_albums WHERE activity_id = %s",
        (activity_id,),
    )

    execute_insert(
        """INSERT INTO activity_albums
           (activity_id, user_id, image_url, description, sort_order, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW())""",
        (activity_id, user_id, image_url, data.get("description", ""), (max_sort["max_sort"] or 0) + 1),
    )

    return success(None, "照片已添加"), 201


# ═══════════════════════════════════════════════════════
# 22. 删除相册照片
# ═══════════════════════════════════════════════════════
@activities_bp.delete("/<int:activity_id>/albums/<int:photo_id>")
@require_auth
def delete_album_photo(activity_id, photo_id):
    """删除活动相册照片（领队或管理员）
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id and g.current_user.get("role") != "admin":
        return error("无权删除", 403)

    execute_update(
        "UPDATE activity_albums SET deleted_at = NOW() WHERE id = %s AND activity_id = %s",
        (photo_id, activity_id),
    )

    return success(None, "照片已删除")


# ═══════════════════════════════════════════════════════
# 23. 活动报告（领队提交活动总结）
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/report-summary")
@require_auth
def submit_activity_report(activity_id):
    """提交活动总结报告（领队）
    ---
    tags:
      - 活动

    # 请求: {actual_count, abnormal_count, abnormal_details, photos, weather_condition, notes}
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id:
        return error("仅领队可以提交活动报告", 403)

    data = request.get_json(silent=True) or {}

    existing = execute_query_one(
        "SELECT id FROM activity_reports WHERE activity_id = %s",
        (activity_id,),
    )
    if existing:
        return error("已提交过活动报告", 409)

    execute_insert(
        """INSERT INTO activity_reports
           (activity_id, captain_id, actual_count, abnormal_count, abnormal_details,
            photos, weather_condition, notes, submitted_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())""",
        (
            activity_id, user_id,
            data.get("actual_count", 0),
            data.get("abnormal_count", 0),
            data.get("abnormal_details"),
            data.get("photos"),
            data.get("weather_condition"),
            data.get("notes"),
        ),
    )

    log_operation(
        operator_id=user_id,
        action="SUBMIT_REPORT",
        target_type="activity",
        target_id=activity_id,
        ip_address=_get_ip(),
    )

    return success(None, "活动报告已提交"), 201


# ═══════════════════════════════════════════════════════
# 24. 站点照片（领队添加场地照片）
# ═══════════════════════════════════════════════════════
@activities_bp.post("/<int:activity_id>/site-photos")
@require_auth
def add_site_photo(activity_id):
    """添加活动场地照片（领队）
    ---
    tags:
      - 活动

    # 请求: {image_url}
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT * FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)
    if activity["captain_id"] != user_id:
        return error("仅领队可以添加场地照片", 403)

    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "")
    if not image_url:
        return error("请提供图片地址", 400)

    max_sort = execute_query_one(
        "SELECT MAX(sort_order) AS max_sort FROM activity_site_photos WHERE activity_id = %s",
        (activity_id,),
    )

    execute_insert(
        """INSERT INTO activity_site_photos
           (activity_id, image_url, sort_order, created_at)
           VALUES (%s, %s, %s, NOW())""",
        (activity_id, image_url, (max_sort["max_sort"] or 0) + 1),
    )

    return success(None, "场地照片已添加"), 201


# ═══════════════════════════════════════════════════════
# 25. 我收藏的活动
# ═══════════════════════════════════════════════════════
@activities_bp.get("/my-favorites")
@require_auth
def my_favorites():
    """获取我收藏的活动列表
    ---
    tags:
      - 活动
    """
    user_id = g.current_user["user_id"]
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    count_sql = """SELECT COUNT(*) AS total
                   FROM activity_favorites f
                   JOIN activities a ON a.id = f.activity_id
                   WHERE f.user_id = %s AND a.deleted_at IS NULL"""
    total = execute_query_one(count_sql, (user_id,))["total"]

    offset = (page - 1) * per_page
    sql = """SELECT a.*, f.created_at AS favorited_at
             FROM activity_favorites f
             JOIN activities a ON a.id = f.activity_id
             WHERE f.user_id = %s AND a.deleted_at IS NULL
             ORDER BY f.created_at DESC
             LIMIT %s OFFSET %s"""
    rows = execute_query(sql, [user_id, per_page, offset])

    return success({
        "activities": [_activity_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })
