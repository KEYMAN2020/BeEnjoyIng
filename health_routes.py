"""健康模块路由 — 2 个 API 端点"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert
from auth_decorator import require_auth
from operation_log import log_operation

health_bp = Blueprint("health", __name__)


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


# ═══════════════════════════════════════════════════════
# 1. 健康申报
# ═══════════════════════════════════════════════════════
@health_bp.post("/declare")
@require_auth
def declare_health():
    """提交健康申报（活动前必须完成）
    ---
    tags:
      - 健康
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            activity_id: {type: integer, description: 活动ID}
            health_status: {type: string, enum: [good, fair, poor], description: 健康状况}
            note: {type: string, description: 备注}
    responses:
      201: {description: 申报成功}
      400: {description: 参数错误}
      401: {description: 未登录}
      409: {description: 已申报过}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    activity_id = data.get("activity_id")
    health_status = data.get("health_status", "good")

    if not activity_id:
        return error("缺少活动 ID", 400)
    if health_status not in ("good", "fair", "poor"):
        return error("健康状况须为 good/fair/poor", 400)

    existing = execute_query_one(
        "SELECT id FROM health_declarations WHERE user_id = %s AND activity_id = %s",
        (user_id, activity_id),
    )
    if existing:
        return error("您已申报过该活动的健康状况", 409)

    decl_id = execute_insert(
        "INSERT INTO health_declarations (user_id, activity_id, health_status, note, declared_at, created_at) VALUES (%s, %s, %s, %s, NOW(), NOW())",
        (user_id, activity_id, health_status, data.get("note", "")),
    )

    execute_query_one(
        "UPDATE activity_signups SET health_confirmed = 1, health_confirmed_at = NOW() WHERE activity_id = %s AND user_id = %s",
        (activity_id, user_id),
    )

    log_operation(
        operator_id=user_id, action="DECLARE_HEALTH", target_type="health",
        target_id=decl_id, detail=f"健康申报 activity_id={activity_id} status={health_status}",
        ip_address=_get_ip(),
    )

    return success({"declaration_id": decl_id}, "健康申报已提交"), 201


# ═══════════════════════════════════════════════════════
# 2. 获取保险信息
# ═══════════════════════════════════════════════════════
@health_bp.get("/insurance/<int:activity_id>")
@require_auth
def get_insurance(activity_id):
    """获取活动保险记录
    ---
    tags:
      - 健康
    parameters:
      - name: activity_id
        in: path
        type: integer
        required: true
        description: 活动ID
    responses:
      200:
        description: 保险记录列表
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                insurance_records:
                  type: array
                  items:
                    type: object
                    properties:
                      id: {type: integer}
                      policy_no: {type: string}
                      provider: {type: string}
                      coverage: {type: string}
                      premium: {type: number}
                      insured_date: {type: string}
                      status: {type: string}
      401: {description: 未登录}
      403: {description: 未参加活动}
      404: {description: 活动不存在}
    """
    user_id = g.current_user["user_id"]

    activity = execute_query_one(
        "SELECT captain_id FROM activities WHERE id = %s AND deleted_at IS NULL",
        (activity_id,),
    )
    if not activity:
        return error("活动不存在", 404)

    if activity["captain_id"] != user_id:
        signup = execute_query_one(
            "SELECT id FROM activity_signups WHERE activity_id = %s AND user_id = %s AND status = 'registered' AND deleted_at IS NULL",
            (activity_id, user_id),
        )
        if not signup:
            return error("您未参加此活动", 403)

    records = execute_query(
        "SELECT * FROM insurance_records WHERE activity_id = %s AND user_id = %s ORDER BY created_at DESC",
        (activity_id, user_id),
    )

    return success({
        "insurance_records": [{
            "id": r["id"], "policy_no": r.get("policy_no"), "provider": r["provider"],
            "coverage": r.get("coverage"), "premium": float(r["premium"]),
            "insured_date": r["insured_date"].isoformat() if hasattr(r["insured_date"], "isoformat") else r["insured_date"],
            "status": r["status"], "claim_no": r.get("claim_no"),
            "claimed_at": r["claimed_at"].isoformat() if r.get("claimed_at") and hasattr(r["claimed_at"], "isoformat") else r.get("claimed_at"),
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in records]
    })
