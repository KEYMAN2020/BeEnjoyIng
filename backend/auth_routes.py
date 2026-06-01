# -*- coding: utf-8 -*-
"""
银发活力平台 — 认证 API 路由
============================
Flask Blueprint，提供用户认证相关接口：
  - 发送验证码（模拟短信）
  - 注册（手机号 + 验证码 + 密码）
  - 登录（手机号 + 密码 → JWT）
  - 刷新 Access Token
  - 退出登录（Token 黑名单）
  - 重置密码（验证码）
  - 修改密码（旧密码验证）
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token

from response import success, ApiError
from utils import (
    is_valid_phone,
    generate_verification_code,
    verify_code,
    verify_password,
    issue_tokens,
)
from models import get_user_by_phone, get_user_auth, create_user_with_profile, update_password


auth_bp = Blueprint("auth", __name__)


def _json():
    """安全解析请求体 JSON，为空时返回空 dict。"""
    return request.get_json(silent=True) or {}


# ═══════════════════════════════════════════════════════
# 1. 发送验证码
# ═══════════════════════════════════════════════════════
@auth_bp.post("/send-code")
def send_code():
    """发送短信验证码（Mock 版，仅打印到控制台）。

    请求体:
        phone (str): 手机号
        purpose (str, optional): 用途，默认 "auth"
    返回:
        code: 0, data: {phone, purpose}
    """
    data = _json()
    phone = data.get("phone")
    purpose = data.get("purpose", "auth")
    if not is_valid_phone(phone):
        raise ApiError("手机号格式错误")
    generate_verification_code(phone, purpose)
    return success({"phone": phone, "purpose": purpose}, "验证码已发送")


# ═══════════════════════════════════════════════════════
# 2. 用户注册
# ═══════════════════════════════════════════════════════
@auth_bp.post("/register")
def register():
    """用户注册。

    流程：校验手机号 → 校验验证码 → 查重 → 创建用户 → 签发 Token。
    请求体:
        phone (str): 手机号
        code (str): 验证码
        password (str): 密码（至少 6 位）
        basic_info (dict, optional): {nickname, avatar_url, gender, ...}
    返回:
        code: 0, data: {user_id, tokens}
    """
    data = _json()
    phone = data.get("phone")
    code = data.get("code")
    password = data.get("password")
    basic_info = data.get("basic_info") or {}

    if not is_valid_phone(phone):
        raise ApiError("手机号格式错误")
    if not code:
        raise ApiError("验证码不能为空")
    if not verify_code(phone, code, "auth"):
        raise ApiError("验证码错误或已过期")
    if get_user_by_phone(phone):
        raise ApiError("手机号已注册")

    user_id = create_user_with_profile(phone, password, basic_info)
    tokens = issue_tokens(user_id)
    return success({"user_id": user_id, "tokens": tokens}, "注册成功")


# ═══════════════════════════════════════════════════════
# 3. 登录
# ═══════════════════════════════════════════════════════
@auth_bp.post("/login")
def login():
    """手机号 + 密码登录，签发 Token。

    注意：手机号不存在和密码错误返回相同提示，防止用户枚举。
    请求体:
        phone (str): 手机号
        password (str): 密码
    返回:
        code: 0, data: {user_id, tokens}
    """
    data = _json()
    phone = data.get("phone")
    password = data.get("password")
    if not is_valid_phone(phone):
        raise ApiError("手机号格式错误")
    user = get_user_by_phone(phone)
    if not user:
        raise ApiError("手机号或密码错误", http_status=401)
    auth = get_user_auth(user["id"])
    if not auth or not verify_password(password, auth.get("auth_value")):
        raise ApiError("手机号或密码错误", http_status=401)
    return success({"user_id": user["id"], "tokens": issue_tokens(user["id"])}, "登录成功")


# ═══════════════════════════════════════════════════════
# 4. 刷新 Access Token
# ═══════════════════════════════════════════════════════
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """用 Refresh Token 换取新的 Access Token。

    请求头:
        Authorization: Bearer <refresh_token>
    返回:
        code: 0, data: {access_token, token_type, expires_in}
    """
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return success({"access_token": access_token, "token_type": "Bearer", "expires_in": 7200})


# ═══════════════════════════════════════════════════════
# 5. 退出登录
# ═══════════════════════════════════════════════════════
@auth_bp.post("/logout")
@jwt_required()
def logout():
    """退出登录，将当前 Token 的 JTI 加入黑名单。

    请求头:
        Authorization: Bearer <access_token>
    返回:
        code: 0
    """
    jti = get_jwt()["jti"]
    from utils import token_blacklist
    token_blacklist.add(jti)
    return success({}, "已退出登录")


# ═══════════════════════════════════════════════════════
# 6. 重置密码（验证码方式）
# ═══════════════════════════════════════════════════════
@auth_bp.post("/reset-password")
def reset_password():
    """通过手机验证码重置密码（无需旧密码）。

    请求体:
        phone (str): 手机号
        code (str): 验证码（需先调用 send-code, purpose=reset_password）
        new_password (str): 新密码
    返回:
        code: 0
    """
    data = _json()
    phone = data.get("phone")
    code = data.get("code")
    new_password = data.get("new_password")
    if not is_valid_phone(phone):
        raise ApiError("手机号格式错误")
    if not verify_code(phone, code, "reset_password"):
        raise ApiError("验证码错误或已过期")
    user = get_user_by_phone(phone)
    if not user:
        raise ApiError("用户不存在", http_status=404)
    update_password(user["id"], new_password)
    return success({}, "密码已重置")


# ═══════════════════════════════════════════════════════
# 7. 修改密码（需旧密码）
# ═══════════════════════════════════════════════════════
@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    """修改密码，需验证旧密码（需登录状态）。

    请求体:
        old_password (str): 旧密码
        new_password (str): 新密码
    请求头:
        Authorization: Bearer <access_token>
    返回:
        code: 0
    """
    data = _json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    user_id = int(get_jwt_identity())
    auth = get_user_auth(user_id)
    if not auth or not verify_password(old_password, auth.get("auth_value")):
        raise ApiError("旧密码错误", http_status=401)
    update_password(user_id, new_password)
    return success({}, "密码已修改")
