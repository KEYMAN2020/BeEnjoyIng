"""合作伙伴模块路由 — 4 个 API 端点"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from operation_log import log_operation

partner_bp = Blueprint("partner", __name__)


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


# ═══════════════════════════════════════════════════════
# 1. 合作伙伴街道列表
# ═══════════════════════════════════════════════════════
@partner_bp.get("/streets")
def list_partner_streets():
    """获取合作伙伴街道列表（公开）
    ---
    tags:
      - 合作伙伴
    responses:
      200:
        description: 街道列表
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                streets:
                  type: array
                  items:
                    type: object
                    properties:
                      user_id: {type: integer}
                      partner_street: {type: string}
                      partner_contact: {type: string}
    """
    rows = execute_query("SELECT * FROM partner_streets ORDER BY partner_street ASC")
    return success({
        "streets": [{
            "user_id": r["user_id"],
            "partner_street": r.get("partner_street", ""),
            "partner_contact": r.get("partner_contact", ""),
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 2. 合作伙伴列表
# ═══════════════════════════════════════════════════════
@partner_bp.get("/profiles")
def list_partner_profiles():
    """获取合作伙伴列表（公开，分页）
    ---
    tags:
      - 合作伙伴
    parameters:
      - name: city
        in: query
        type: string
        required: false
        description: 城市筛选
      - name: district
        in: query
        type: string
        required: false
        description: 区域筛选
      - name: status
        in: query
        type: string
        required: false
        default: active
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
        description: 合作伙伴列表
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                profiles: {type: array}
                total: {type: integer}
                page: {type: integer}
                per_page: {type: integer}
    """
    city = request.args.get("city", "")
    district = request.args.get("district", "")
    status = request.args.get("status", "active")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    conditions = ["p.deleted_at IS NULL"]
    params = []
    if city:
        conditions.append("p.city = %s"); params.append(city)
    if district:
        conditions.append("p.district = %s"); params.append(district)
    if status:
        conditions.append("p.status = %s"); params.append(status)

    where = " AND ".join(conditions)
    total = execute_query_one(f"SELECT COUNT(*) AS total FROM partner_profiles p WHERE {where}", params)["total"]

    offset = (page - 1) * per_page
    rows = execute_query(
        f"SELECT p.*, u.nickname, u.avatar_url FROM partner_profiles p JOIN users u ON u.id = p.user_id WHERE {where} ORDER BY p.created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset],
    )

    return success({
        "profiles": [{
            "user_id": r["user_id"], "nickname": r["nickname"], "avatar_url": r.get("avatar_url", ""),
            "name": r["name"], "city": r["city"], "district": r["district"],
            "address": r.get("address", ""), "contact_name": r["contact_name"],
            "contact_phone": r["contact_phone"], "contact_position": r.get("contact_position"),
            "venues": r.get("venues"), "status": r["status"],
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in rows],
        "total": total, "page": page, "per_page": per_page,
    })


# ═══════════════════════════════════════════════════════
# 3. 合作伙伴详情
# ═══════════════════════════════════════════════════════
@partner_bp.get("/profiles/<int:user_id>")
def get_partner_profile(user_id):
    """获取合作伙伴详情（公开）
    ---
    tags:
      - 合作伙伴
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200: {description: 合作伙伴详情}
      404: {description: 不存在}
    """
    profile = execute_query_one(
        "SELECT p.*, u.nickname, u.avatar_url FROM partner_profiles p JOIN users u ON u.id = p.user_id WHERE p.user_id = %s AND p.deleted_at IS NULL",
        (user_id,),
    )
    if not profile:
        return error("合作伙伴不存在", 404)

    return success({
        "profile": {k: profile[k] for k in (
            "user_id", "nickname", "name", "city", "district", "address",
            "contact_name", "contact_phone", "contact_position", "venues",
            "status", "ext_data",
        )}
    })


# ═══════════════════════════════════════════════════════
# 4. 申请成为合作伙伴
# ═══════════════════════════════════════════════════════
@partner_bp.post("/apply")
@require_auth
def apply_partner():
    """申请成为合作伙伴（需登录）
    ---
    tags:
      - 合作伙伴
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name: {type: string, description: 机构名称}
            city: {type: string}
            district: {type: string}
            contact_name: {type: string}
            contact_phone: {type: string}
            address: {type: string}
            venues: {type: string, description: 场地信息}
            partner_street: {type: string, description: 所属街道}
    responses:
      201: {description: 申请成功}
      400: {description: 缺少必填字段}
      401: {description: 未登录}
      409: {description: 已是合作伙伴}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    required = ["name", "city", "district", "contact_name", "contact_phone"]
    for field in required:
        if not data.get(field):
            return error(f"缺少必填字段: {field}", 400)

    existing = execute_query_one(
        "SELECT user_id FROM partner_profiles WHERE user_id = %s AND deleted_at IS NULL", (user_id,),
    )
    if existing:
        return error("您已是合作伙伴", 409)

    execute_insert(
        "INSERT INTO partner_profiles (user_id, name, city, district, address, contact_name, contact_phone, contact_position, venues, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())",
        (user_id, data["name"], data["city"], data["district"], data.get("address", ""), data["contact_name"], data["contact_phone"], data.get("contact_position"), data.get("venues")),
    )

    partner_street = data.get("partner_street", "")
    if partner_street:
        existing_street = execute_query_one("SELECT user_id FROM partner_streets WHERE user_id = %s", (user_id,))
        if existing_street:
            execute_update("UPDATE partner_streets SET partner_street = %s, partner_contact = %s, updated_at = NOW() WHERE user_id = %s", (partner_street, data["contact_name"], user_id))
        else:
            execute_insert("INSERT INTO partner_streets (user_id, partner_street, partner_contact, updated_at) VALUES (%s, %s, %s, NOW())", (user_id, partner_street, data["contact_name"]))

    log_operation(operator_id=user_id, action="APPLY_PARTNER", target_type="partner", target_id=user_id, ip_address=_get_ip())
    return success({"user_id": user_id}, "申请已提交"), 201
