"""支付模块路由 — 7 个 API 端点

路由前缀: /api/v1/payment
"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from operation_log import log_operation

payment_bp = Blueprint("payment", __name__)


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


# ═══════════════════════════════════════════════════════
# 1. 创建支付
# ═══════════════════════════════════════════════════════
@payment_bp.post("/create")
@require_auth
def create_payment():
    """创建支付记录

    请求: {signup_id, activity_id, amount, payment_method}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    signup_id = data.get("signup_id")
    activity_id = data.get("activity_id")
    amount = data.get("amount", type=float)
    payment_method = data.get("payment_method", "")

    if not all([signup_id, activity_id, amount, payment_method]):
        return error("缺少必填参数", 400)

    payment_id = execute_insert(
        """INSERT INTO payment_records
           (signup_id, user_id, activity_id, amount, payment_method, status, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, 'pending', NOW(), NOW())""",
        (signup_id, user_id, activity_id, amount, payment_method),
    )

    log_operation(
        operator_id=user_id,
        action="CREATE_PAYMENT",
        target_type="payment",
        target_id=payment_id,
        detail=f"创建支付 {amount}元 method={payment_method}",
        ip_address=_get_ip(),
    )

    return success({
        "payment_id": payment_id,
        "amount": amount,
        "status": "pending",
    }, "支付已创建"), 201


# ═══════════════════════════════════════════════════════
# 2. 支付记录列表
# ═══════════════════════════════════════════════════════
@payment_bp.get("/records")
@require_auth
def list_payments():
    """获取支付记录列表

    查询参数: status, page, per_page
    """
    user_id = g.current_user["user_id"]
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    conditions = ["p.user_id = %s", "p.deleted_at IS NULL"]
    params = [user_id]

    if status:
        conditions.append("p.status = %s")
        params.append(status)

    where = " AND ".join(conditions)

    count_sql = f"SELECT COUNT(*) AS total FROM payment_records p WHERE {where}"
    total = execute_query_one(count_sql, params)["total"]

    offset = (page - 1) * per_page
    sql = f"""SELECT p.*, a.title AS activity_title
              FROM payment_records p
              LEFT JOIN activities a ON a.id = p.activity_id
              WHERE {where}
              ORDER BY p.created_at DESC
              LIMIT %s OFFSET %s"""
    rows = execute_query(sql, params + [per_page, offset])

    return success({
        "records": [{
            "id": r["id"],
            "signup_id": r["signup_id"],
            "activity_id": r["activity_id"],
            "activity_title": r.get("activity_title", ""),
            "amount": float(r["amount"]),
            "refund_amount": float(r["refund_amount"]) if r.get("refund_amount") else 0,
            "payment_method": r["payment_method"],
            "status": r["status"],
            "paid_at": r["paid_at"].isoformat() if r.get("paid_at") and hasattr(r["paid_at"], "isoformat") else r.get("paid_at"),
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ═══════════════════════════════════════════════════════
# 3. 支付详情
# ═══════════════════════════════════════════════════════
@payment_bp.get("/records/<int:payment_id>")
@require_auth
def get_payment(payment_id):
    """获取支付记录详情"""
    user_id = g.current_user["user_id"]
    role = g.current_user.get("role", "user")

    record = execute_query_one(
        "SELECT p.*, a.title AS activity_title FROM payment_records p LEFT JOIN activities a ON a.id = p.activity_id WHERE p.id = %s AND p.deleted_at IS NULL",
        (payment_id,),
    )
    if not record:
        return error("支付记录不存在", 404)
    if record["user_id"] != user_id and role != "admin":
        return error("无权查看", 403)

    return success({
        "record": {
            "id": record["id"],
            "signup_id": record["signup_id"],
            "user_id": record["user_id"],
            "activity_id": record["activity_id"],
            "activity_title": record.get("activity_title", ""),
            "amount": float(record["amount"]),
            "refund_amount": float(record["refund_amount"]) if record.get("refund_amount") else 0,
            "payment_method": record["payment_method"],
            "channel_order_id": record.get("channel_order_id"),
            "channel_trade_no": record.get("channel_trade_no"),
            "status": record["status"],
            "paid_at": record["paid_at"].isoformat() if record.get("paid_at") and hasattr(record["paid_at"], "isoformat") else record.get("paid_at"),
            "refunded_at": record["refunded_at"].isoformat() if record.get("refunded_at") and hasattr(record["refunded_at"], "isoformat") else record.get("refunded_at"),
            "refund_reason": record.get("refund_reason"),
            "expire_at": record["expire_at"].isoformat() if record.get("expire_at") and hasattr(record["expire_at"], "isoformat") else record.get("expire_at"),
            "created_at": record["created_at"].isoformat() if hasattr(record["created_at"], "isoformat") else record["created_at"],
        }
    })


# ═══════════════════════════════════════════════════════
# 4. 申请退款
# ═══════════════════════════════════════════════════════
@payment_bp.post("/<int:payment_id>/refund")
@require_auth
def request_refund(payment_id):
    """申请退款

    请求: {reason?}
    """
    user_id = g.current_user["user_id"]

    record = execute_query_one(
        "SELECT * FROM payment_records WHERE id = %s AND deleted_at IS NULL",
        (payment_id,),
    )
    if not record:
        return error("支付记录不存在", 404)
    if record["user_id"] != user_id:
        return error("无权操作", 403)
    if record["status"] != "paid":
        return error("只有已支付的订单可以退款", 400)

    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "")

    execute_update(
        "UPDATE payment_records SET status = 'refunding', refund_reason = %s, updated_at = NOW() WHERE id = %s",
        (reason, payment_id),
    )

    log_operation(
        operator_id=user_id,
        action="REQUEST_REFUND",
        target_type="payment",
        target_id=payment_id,
        detail=f"申请退款: {reason}",
        ip_address=_get_ip(),
    )

    return success(None, "退款申请已提交")


# ═══════════════════════════════════════════════════════
# 5. 创建订阅
# ═══════════════════════════════════════════════════════
@payment_bp.post("/subscription")
@require_auth
def create_subscription():
    """创建会员订阅

    请求: {plan_type, amount, payment_method, auto_renew?}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    plan_type = data.get("plan_type", "")
    amount = data.get("amount", type=float)
    payment_method = data.get("payment_method", "")

    if not plan_type or not amount or not payment_method:
        return error("缺少必填参数", 400)

    # 检查现有订阅
    existing = execute_query_one(
        "SELECT id FROM premium_subscriptions WHERE user_id = %s AND status = 'active' AND deleted_at IS NULL",
        (user_id,),
    )
    if existing:
        return error("您已有有效订阅", 409)

    # 计算起止日期（按月）
    from datetime import datetime, timedelta
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    sub_id = execute_insert(
        """INSERT INTO premium_subscriptions
           (user_id, plan_type, start_date, end_date, auto_renew, status,
            payment_method, amount, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, 'active', %s, %s, NOW(), NOW())""",
        (
            user_id, plan_type, start_date, end_date,
            data.get("auto_renew", True),
            payment_method, amount,
        ),
    )

    log_operation(
        operator_id=user_id,
        action="CREATE_SUBSCRIPTION",
        target_type="subscription",
        target_id=sub_id,
        detail=f"创建订阅 {plan_type} {amount}元",
        ip_address=_get_ip(),
    )

    return success({
        "subscription_id": sub_id,
        "plan_type": plan_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
    }, "订阅已创建"), 201


# ═══════════════════════════════════════════════════════
# 6. 获取订阅信息
# ═══════════════════════════════════════════════════════
@payment_bp.get("/subscription")
@require_auth
def get_subscription():
    """获取我的订阅信息"""
    user_id = g.current_user["user_id"]

    sub = execute_query_one(
        "SELECT * FROM premium_subscriptions WHERE user_id = %s AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if not sub:
        return success({"subscription": None}, "无订阅信息")

    return success({
        "subscription": {
            "id": sub["id"],
            "plan_type": sub["plan_type"],
            "start_date": sub["start_date"].isoformat() if hasattr(sub["start_date"], "isoformat") else sub["start_date"],
            "end_date": sub["end_date"].isoformat() if hasattr(sub["end_date"], "isoformat") else sub["end_date"],
            "auto_renew": bool(sub["auto_renew"]),
            "status": sub["status"],
            "amount": float(sub["amount"]),
            "payment_method": sub.get("payment_method"),
            "created_at": sub["created_at"].isoformat() if hasattr(sub["created_at"], "isoformat") else sub["created_at"],
        }
    })


# ═══════════════════════════════════════════════════════
# 7. 取消订阅
# ═══════════════════════════════════════════════════════
@payment_bp.post("/subscription/cancel")
@require_auth
def cancel_subscription():
    """取消会员订阅"""
    user_id = g.current_user["user_id"]

    sub = execute_query_one(
        "SELECT id FROM premium_subscriptions WHERE user_id = %s AND status = 'active' AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if not sub:
        return error("没有有效的订阅", 404)

    execute_update(
        "UPDATE premium_subscriptions SET status = 'cancelled', auto_renew = 0, updated_at = NOW() WHERE id = %s",
        (sub["id"],),
    )

    log_operation(
        operator_id=user_id,
        action="CANCEL_SUBSCRIPTION",
        target_type="subscription",
        target_id=sub["id"],
        ip_address=_get_ip(),
    )

    return success(None, "订阅已取消")
