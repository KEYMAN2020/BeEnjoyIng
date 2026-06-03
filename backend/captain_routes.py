"""领队模块路由 — 6 个 API 端点

路由前缀: /api/v1/captain
"""

from flask import Blueprint, request, g
from response import success, error
from db import execute_query, execute_query_one, execute_insert, execute_update
from auth_decorator import require_auth
from operation_log import log_operation

captain_bp = Blueprint("captain", __name__)


def _get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


# ═══════════════════════════════════════════════════════
# 1. 申请成为领队
# ═══════════════════════════════════════════════════════
@captain_bp.post("/apply")
@require_auth
def apply_captain():
    """申请成为领队

    请求: {real_name, phone, id_card_last4?, bio, experience, preferred_categories?}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    real_name = data.get("real_name", "")
    phone = data.get("phone", "")
    if not real_name:
        return error("请填写真实姓名", 400)
    if not phone:
        return error("请填写联系电话", 400)

    # 检查是否已有申请
    existing = execute_query_one(
        "SELECT id, status FROM captain_applications WHERE user_id = %s AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if existing:
        if existing["status"] == "pending":
            return error("已有审核中的申请", 409)
        if existing["status"] == "approved":
            return error("您已是认证领队", 409)

    # 检查 captain_profiles 是否存在
    profile = execute_query_one(
        "SELECT user_id FROM captain_profiles WHERE user_id = %s",
        (user_id,),
    )

    app_id = execute_insert(
        """INSERT INTO captain_applications
           (user_id, real_name, phone, id_card_last4, bio, experience,
            preferred_categories, status, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW())""",
        (
            user_id, real_name, phone,
            data.get("id_card_last4"),
            data.get("bio", ""),
            data.get("experience", ""),
            data.get("preferred_categories", ""),
        ),
    )

    if not profile:
        execute_insert(
            """INSERT INTO captain_profiles
               (user_id, captain_since, captain_status, captain_rating, updated_at)
               VALUES (%s, NULL, 'pending', 0.0, NOW())""",
            (user_id,),
        )

    log_operation(
        operator_id=user_id,
        action="APPLY_CAPTAIN",
        target_type="captain",
        target_id=app_id,
        ip_address=_get_ip(),
    )

    return success({"application_id": app_id}, "申请已提交，等待审核"), 201


# ═══════════════════════════════════════════════════════
# 2. 查看我的申请状态
# ═══════════════════════════════════════════════════════
@captain_bp.get("/application")
@require_auth
def get_application():
    """获取我的领队申请状态"""
    user_id = g.current_user["user_id"]

    app = execute_query_one(
        "SELECT * FROM captain_applications WHERE user_id = %s AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if not app:
        return error("未找到申请记录", 404)

    return success({
        "application": {
            "id": app["id"],
            "real_name": app["real_name"],
            "phone": app["phone"],
            "status": app["status"],
            "review_comment": app.get("review_comment"),
            "reviewed_at": app["reviewed_at"].isoformat() if app.get("reviewed_at") and hasattr(app["reviewed_at"], "isoformat") else app.get("reviewed_at"),
            "created_at": app["created_at"].isoformat() if hasattr(app["created_at"], "isoformat") else app["created_at"],
        }
    })


# ═══════════════════════════════════════════════════════
# 3. 获取领队资料
# ═══════════════════════════════════════════════════════
@captain_bp.get("/profile")
@require_auth
def get_captain_profile():
    """获取我的领队资料"""
    user_id = g.current_user["user_id"]

    profile = execute_query_one(
        "SELECT * FROM captain_profiles WHERE user_id = %s",
        (user_id,),
    )
    if not profile:
        return error("您还不是领队", 404)

    # 获取最近一次申请
    app = execute_query_one(
        "SELECT * FROM captain_applications WHERE user_id = %s AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
        (user_id,),
    )

    # 获取培训记录
    trainings = execute_query(
        "SELECT * FROM captain_training WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )

    return success({
        "profile": {
            "user_id": profile["user_id"],
            "captain_since": profile["captain_since"].isoformat() if profile.get("captain_since") and hasattr(profile["captain_since"], "isoformat") else profile.get("captain_since"),
            "captain_status": profile.get("captain_status", "pending"),
            "captain_rating": float(profile.get("captain_rating", 0)),
            "captain_bio": profile.get("captain_bio", ""),
            "training_completed": bool(profile["training_completed"]),
            "training_completed_at": profile["training_completed_at"].isoformat() if profile.get("training_completed_at") and hasattr(profile["training_completed_at"], "isoformat") else profile.get("training_completed_at"),
        },
        "application": {
            "real_name": app["real_name"] if app else "",
            "phone": app["phone"] if app else "",
            "status": app["status"] if app else "",
        } if app else None,
        "trainings": [{
            "id": t["id"],
            "training_type": t["training_type"],
            "score": t.get("score"),
            "passed": bool(t["passed"]),
            "passed_at": t["passed_at"].isoformat() if t.get("passed_at") and hasattr(t["passed_at"], "isoformat") else t.get("passed_at"),
            "expire_at": t["expire_at"].isoformat() if t.get("expire_at") and hasattr(t["expire_at"], "isoformat") else t.get("expire_at"),
        } for t in trainings],
    })


# ═══════════════════════════════════════════════════════
# 4. 更新领队资料
# ═══════════════════════════════════════════════════════
@captain_bp.put("/profile")
@require_auth
def update_captain_profile():
    """更新领队资料

    请求: {captain_bio, preferred_categories?}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    profile = execute_query_one(
        "SELECT user_id FROM captain_profiles WHERE user_id = %s",
        (user_id,),
    )
    if not profile:
        return error("您还不是领队", 404)

    updates = []
    params = []

    if "captain_bio" in data:
        updates.append("captain_bio = %s")
        params.append(data["captain_bio"])

    if not updates:
        return error("没有需要更新的字段", 400)

    updates.append("updated_at = NOW()")
    params.append(user_id)

    execute_update(
        f"UPDATE captain_profiles SET {', '.join(updates)} WHERE user_id = %s",
        params,
    )

    # 更新申请表中的偏好分类
    if "preferred_categories" in data:
        execute_update(
            "UPDATE captain_applications SET preferred_categories = %s WHERE user_id = %s AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
            (data["preferred_categories"], user_id),
        )

    log_operation(
        operator_id=user_id,
        action="UPDATE_CAPTAIN_PROFILE",
        target_type="captain",
        target_id=user_id,
        ip_address=_get_ip(),
    )

    return success(None, "资料已更新")


# ═══════════════════════════════════════════════════════
# 5. 获取培训记录
# ═══════════════════════════════════════════════════════
@captain_bp.get("/training")
@require_auth
def get_trainings():
    """获取我的培训记录"""
    user_id = g.current_user["user_id"]

    rows = execute_query(
        "SELECT * FROM captain_training WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )

    return success({
        "trainings": [{
            "id": r["id"],
            "training_type": r["training_type"],
            "content": r.get("content", ""),
            "score": r.get("score"),
            "passed": bool(r["passed"]),
            "trainer": r.get("trainer", ""),
            "passed_at": r["passed_at"].isoformat() if r.get("passed_at") and hasattr(r["passed_at"], "isoformat") else r.get("passed_at"),
            "expire_at": r["expire_at"].isoformat() if r.get("expire_at") and hasattr(r["expire_at"], "isoformat") else r.get("expire_at"),
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else r["created_at"],
        } for r in rows]
    })


# ═══════════════════════════════════════════════════════
# 6. 提交培训记录
# ═══════════════════════════════════════════════════════
@captain_bp.post("/training")
@require_auth
def submit_training():
    """提交培训完成记录

    请求: {training_type, content?, score?, trainer?, expire_at?}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    training_type = data.get("training_type", "")
    if not training_type:
        return error("请填写培训类型", 400)

    score = data.get("score", type=int)
    passed = score is not None and score >= 60 if score is not None else True

    training_id = execute_insert(
        """INSERT INTO captain_training
           (user_id, training_type, content, score, passed, trainer, passed_at, expire_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, NOW(), NOW())""",
        (
            user_id, training_type,
            data.get("content", ""),
            score, passed,
            data.get("trainer", ""),
            data.get("expire_at"),
        ),
    )

    # 更新 captain_profiles
    if passed:
        execute_update(
            "UPDATE captain_profiles SET training_completed = 1, training_completed_at = NOW(), updated_at = NOW() WHERE user_id = %s",
            (user_id,),
        )

    log_operation(
        operator_id=user_id,
        action="SUBMIT_TRAINING",
        target_type="captain",
        target_id=user_id,
        detail=f"培训: {training_type} score={score}",
        ip_address=_get_ip(),
    )

    return success({"training_id": training_id}, "培训记录已提交"), 201


# ═══════════════════════════════════════════════════════
# 7. 审核领队申请（管理员）
# ═══════════════════════════════════════════════════════
@captain_bp.post("/review/<int:application_id>")
@require_auth
def review_application(application_id):
    """审核领队申请（管理员）

    请求: {action: "approve"/"reject", comment?}
    """
    user_id = g.current_user["user_id"]
    role = g.current_user.get("role", "user")
    if role != "admin":
        return error("仅管理员可以审核", 403)

    app = execute_query_one(
        "SELECT * FROM captain_applications WHERE id = %s AND deleted_at IS NULL",
        (application_id,),
    )
    if not app:
        return error("申请不存在", 404)
    if app["status"] != "pending":
        return error("该申请已经审核", 400)

    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    if action not in ("approve", "reject"):
        return error("审核操作必须为 approve 或 reject", 400)

    new_status = "approved" if action == "approve" else "rejected"
    execute_update(
        "UPDATE captain_applications SET status = %s, review_comment = %s, reviewed_by = %s, reviewed_at = NOW(), updated_at = NOW() WHERE id = %s",
        (new_status, data.get("comment", ""), user_id, application_id),
    )

    # 更新 captain_profiles
    if action == "approve":
        execute_update(
            "UPDATE captain_profiles SET captain_status = 'active', captain_since = NOW(), updated_at = NOW() WHERE user_id = %s",
            (app["user_id"],),
        )
        # 更新 users 表 role
        execute_update(
            "UPDATE users SET role = 'captain', updated_at = NOW() WHERE id = %s",
            (app["user_id"],),
        )

    log_operation(
        operator_id=user_id,
        action=f"REVIEW_CAPTAIN_{action.upper()}",
        target_type="captain",
        target_id=application_id,
        ip_address=_get_ip(),
    )

    return success(None, f"申请已{'通过' if action == 'approve' else '驳回'}")
