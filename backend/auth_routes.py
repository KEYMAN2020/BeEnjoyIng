"""认证模块路由 — 9 个 API 端点

路由前缀: /api/v1/auth
"""

from flask import Blueprint, request, g
from werkzeug.security import generate_password_hash, check_password_hash

from response import success, error
from utils import is_valid_phone, verify_code, generate_verification_code
from db import execute_query_one, execute_insert, execute_update
from jwt_helper import generate_access_token, generate_refresh_token, decode_token
from auth_decorator import require_auth
from operation_log import log_operation

auth_bp = Blueprint("auth", __name__)


# ── 辅助函数 ─────────────────────────────────────────────


def _get_ip():
    """获取请求 IP"""
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")


def _user_to_dict(user: dict) -> dict:
    """将用户记录转为安全的返回字典"""
    return {
        "user_id": user["id"],
        "phone": user["phone"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url", ""),
        "role": user["role"],
        "is_banned": bool(user["is_banned"]),
        "created_at": user["created_at"].isoformat() if hasattr(user.get("created_at"), "isoformat") else user["created_at"],
    }


def _login_response(user: dict) -> tuple:
    """生成登录成功响应（含 token）"""
    access_token = generate_access_token(user["id"], user["role"])
    refresh_token = generate_refresh_token(user["id"])
    return success({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 1800,
        "user": _user_to_dict(user),
    }, "登录成功")


# ═══════════════════════════════════════════════════════
# 1. 发送验证码
# ═══════════════════════════════════════════════════════
@auth_bp.post("/send-code")
def send_code():
    """发送验证码（Mock 版，打印到控制台）

    请求: {"phone": "13800138000"}
    响应: {"code": 0, "data": {"expire_in": 300}, "message": "验证码已发送"}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")

    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)

    generate_verification_code(phone, purpose="login")

    # 查一下该手机号是否有用户（仅用于日志，不影响流程）
    user = execute_query_one("SELECT id FROM users WHERE phone = %s AND deleted_at IS NULL", (phone,))
    log_operation(
        operator_id=user["id"] if user else 0,
        action="SEND_CODE",
        target_type="auth",
        detail=f"发送验证码 phone={phone}",
        ip_address=_get_ip(),
    )

    return success({"expire_in": 300}, "验证码已发送")


# ═══════════════════════════════════════════════════════
# 2. 注册
# ═══════════════════════════════════════════════════════
@auth_bp.post("/register")
def register():
    """手机号 + 验证码 + 密码 注册

    请求: {"phone": "13800138000", "code": "123456", "password": "abc123", "nickname": "王阿姨"}
    响应: {"code": 0, "data": {"access_token": "...", "user": {...}}}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    code = data.get("code", "")
    password = data.get("password", "")
    nickname = data.get("nickname", "")

    # 校验
    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)
    if not password or len(password) < 6:
        return error("密码至少 6 位", 400)
    if not verify_code(phone, code, purpose="login"):
        return error("验证码错误或已过期", 400)
    if not nickname:
        nickname = f"用户{phone[-4:]}"

    # 查重
    existing = execute_query_one(
        "SELECT id FROM users WHERE phone = %s AND deleted_at IS NULL", (phone,)
    )
    if existing:
        return error("该手机号已注册", 409)

    # 创建用户
    user_id = execute_insert(
        "INSERT INTO users (phone, nickname, role, created_at, updated_at) VALUES (%s, %s, 'user', NOW(), NOW())",
        (phone, nickname),
    )

    # 存储密码
    pwd_hash = generate_password_hash(password)
    execute_insert(
        "INSERT INTO user_auth (user_id, auth_type, auth_value, created_at) VALUES (%s, 'password', %s, NOW())",
        (user_id, pwd_hash),
    )

    # 创建空 profile
    execute_insert(
        "INSERT INTO user_profiles (user_id, updated_at) VALUES (%s, NOW())",
        (user_id,),
    )

    log_operation(
        operator_id=user_id,
        action="REGISTER",
        target_type="user",
        target_id=user_id,
        detail=f"用户注册 phone={phone}",
        ip_address=_get_ip(),
    )

    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at FROM users WHERE id = %s",
        (user_id,),
    )
    return _login_response(user), 201


# ═══════════════════════════════════════════════════════
# 3. 密码登录
# ═══════════════════════════════════════════════════════
@auth_bp.post("/login")
def login():
    """手机号 + 密码登录

    请求: {"phone": "13800138000", "password": "abc123"}
    响应: {"code": 0, "data": {"access_token": "...", "refresh_token": "...", "user": {...}}}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    password = data.get("password", "")

    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)
    if not password:
        return error("请输入密码", 400)

    # 查用户
    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at FROM users WHERE phone = %s AND deleted_at IS NULL",
        (phone,),
    )
    if not user:
        return error("用户不存在", 404)

    if user["is_banned"]:
        return error("账号已被禁用", 403)

    # 查密码
    auth_record = execute_query_one(
        "SELECT auth_value FROM user_auth WHERE user_id = %s AND auth_type = 'password'",
        (user["id"],),
    )
    if not auth_record or not check_password_hash(auth_record["auth_value"], password):
        return error("密码错误", 401)

    log_operation(
        operator_id=user["id"],
        action="LOGIN",
        target_type="user",
        target_id=user["id"],
        detail="密码登录",
        ip_address=_get_ip(),
    )

    return _login_response(user)


# ═══════════════════════════════════════════════════════
# 4. 验证码登录
# ═══════════════════════════════════════════════════════
@auth_bp.post("/login-code")
def login_code():
    """手机号 + 验证码登录（不存在则自动注册）

    请求: {"phone": "13800138000", "code": "123456"}
    响应: {"code": 0, "data": {"access_token": "...", "user": {...}}}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    code = data.get("code", "")

    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)
    if not verify_code(phone, code, purpose="login"):
        return error("验证码错误或已过期", 400)

    # 查找或创建用户
    user = execute_query_one(
        "SELECT id, phone, nickname, avatar_url, role, is_banned, created_at FROM users WHERE phone = %s AND deleted_at IS NULL",
        (phone,),
    )
    if user:
        if user["is_banned"]:
            return error("账号已被禁用", 403)
        user_id = user["id"]
    else:
        # 自动注册
        nickname = f"用户{phone[-4:]}"
        user_id = execute_insert(
            "INSERT INTO users (phone, nickname, role, created_at, updated_at) VALUES (%s, %s, 'user', NOW(), NOW())",
            (phone, nickname),
        )
        execute_insert(
            "INSERT INTO user_profiles (user_id, updated_at) VALUES (%s, NOW())",
            (user_id,),
        )
        user = {
            "id": user_id,
            "phone": phone,
            "nickname": nickname,
            "avatar_url": None,
            "role": "user",
            "is_banned": 0,
            "created_at": None,
        }

    log_operation(
        operator_id=user_id,
        action="LOGIN_CODE",
        target_type="user",
        target_id=user_id,
        detail="验证码登录",
        ip_address=_get_ip(),
    )

    return _login_response(user)


# ═══════════════════════════════════════════════════════
# 5. 刷新令牌
# ═══════════════════════════════════════════════════════
@auth_bp.post("/refresh")
def refresh():
    """用 refresh_token 换取新的 access_token

    请求: {"refresh_token": "..."}
    响应: {"code": 0, "data": {"access_token": "...", "expires_in": 1800}}
    """
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return error("缺少 refresh_token", 400)

    payload = decode_token(refresh_token)
    if payload is None:
        return error("刷新令牌无效或已过期", 401)
    if payload.get("type") != "refresh":
        return error("令牌类型错误", 401)

    # 确认用户仍存在且未被禁用
    user = execute_query_one(
        "SELECT id, role, is_banned FROM users WHERE id = %s AND deleted_at IS NULL",
        (payload["user_id"],),
    )
    if not user:
        return error("用户不存在", 404)
    if user["is_banned"]:
        return error("账号已被禁用", 403)

    new_access_token = generate_access_token(user["id"], user["role"])
    return success({
        "access_token": new_access_token,
        "expires_in": 1800,
    }, "令牌已刷新")


# ═══════════════════════════════════════════════════════
# 6. 登出
# ═══════════════════════════════════════════════════════
@auth_bp.post("/logout")
@require_auth
def logout():
    """登出（当前为无状态登出，客户端自行丢弃令牌）"""
    user_id = g.current_user["user_id"]

    log_operation(
        operator_id=user_id,
        action="LOGOUT",
        target_type="user",
        target_id=user_id,
        ip_address=_get_ip(),
    )

    return success(None, "已登出")


# ═══════════════════════════════════════════════════════
# 7. 重置密码
# ═══════════════════════════════════════════════════════
@auth_bp.post("/reset-password")
def reset_password():
    """验证码验证身份后重置密码

    请求: {"phone": "13800138000", "code": "123456", "new_password": "newpass123"}
    响应: {"code": 0, "data": {}, "message": "密码已重置"}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    code = data.get("code", "")
    new_password = data.get("new_password", "")

    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)
    if not new_password or len(new_password) < 6:
        return error("密码至少 6 位", 400)
    if not verify_code(phone, code, purpose="login"):
        return error("验证码错误或已过期", 400)

    user = execute_query_one(
        "SELECT id FROM users WHERE phone = %s AND deleted_at IS NULL", (phone,)
    )
    if not user:
        return error("用户不存在", 404)

    pwd_hash = generate_password_hash(new_password)

    # 更新或插入密码
    existing = execute_query_one(
        "SELECT id FROM user_auth WHERE user_id = %s AND auth_type = 'password'",
        (user["id"],),
    )
    if existing:
        execute_update(
            "UPDATE user_auth SET auth_value = %s, updated_at = NOW() WHERE id = %s",
            (pwd_hash, existing["id"]),
        )
    else:
        execute_insert(
            "INSERT INTO user_auth (user_id, auth_type, auth_value, created_at) VALUES (%s, 'password', %s, NOW())",
            (user["id"], pwd_hash),
        )

    log_operation(
        operator_id=user["id"],
        action="RESET_PASSWORD",
        target_type="user",
        target_id=user["id"],
        ip_address=_get_ip(),
    )

    return success(None, "密码已重置")


# ═══════════════════════════════════════════════════════
# 8. 修改密码
# ═══════════════════════════════════════════════════════
@auth_bp.post("/change-password")
@require_auth
def change_password():
    """已登录用户修改密码

    请求: {"old_password": "xxx", "new_password": "yyy"}
    响应: {"code": 0, "data": {}, "message": "密码已修改"}
    """
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    user_id = g.current_user["user_id"]

    if not old_password:
        return error("请输入原密码", 400)
    if not new_password or len(new_password) < 6:
        return error("新密码至少 6 位", 400)
    if old_password == new_password:
        return error("新密码不能与旧密码相同", 400)

    # 验证原密码
    auth_record = execute_query_one(
        "SELECT id, auth_value FROM user_auth WHERE user_id = %s AND auth_type = 'password'",
        (user_id,),
    )
    if not auth_record:
        return error("未设置密码，请使用验证码登录", 400)
    if not check_password_hash(auth_record["auth_value"], old_password):
        return error("原密码错误", 401)

    # 更新密码
    pwd_hash = generate_password_hash(new_password)
    execute_update(
        "UPDATE user_auth SET auth_value = %s WHERE id = %s",
        (pwd_hash, auth_record["id"]),
    )

    log_operation(
        operator_id=user_id,
        action="CHANGE_PASSWORD",
        target_type="user",
        target_id=user_id,
        ip_address=_get_ip(),
    )

    return success(None, "密码已修改")


# ═══════════════════════════════════════════════════════
# 9. 验证身份
# ═══════════════════════════════════════════════════════
@auth_bp.post("/verify-identity")
def verify_identity():
    """通过验证码验证手机号身份（不发令牌，仅确认）

    请求: {"phone": "13800138000", "code": "123456"}
    响应: {"code": 0, "data": {"verified": true}, "message": "身份验证通过"}
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    code = data.get("code", "")

    if not is_valid_phone(phone):
        return error("手机号格式错误", 400)
    if not verify_code(phone, code, purpose="login"):
        return error("验证码错误或已过期", 400)

    user = execute_query_one(
        "SELECT id FROM users WHERE phone = %s AND deleted_at IS NULL", (phone,)
    )
    log_operation(
        operator_id=user["id"] if user else 0,
        action="VERIFY_IDENTITY",
        target_type="auth",
        detail=f"身份验证 phone={phone}",
        ip_address=_get_ip(),
    )

    return success({"verified": True}, "身份验证通过")
