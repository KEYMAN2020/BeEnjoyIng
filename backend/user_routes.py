# -*- coding: utf-8 -*-
"""
银发活力平台 — 用户资料 API 路由
=================================
Flask Blueprint，提供用户资料相关接口：
  - 查看本人资料（需登录）
  - 更新本人资料（需登录）
  - 查看他人公开资料（无需登录）
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from response import ApiError, success
from models import get_user_profile, update_profile, public_user_fields

user_bp = Blueprint("users", __name__)


def _json():
    """安全解析请求体 JSON，为空时返回空 dict。"""
    return request.get_json(silent=True) or {}


# ═══════════════════════════════════════════════════════
# 查看本人资料
# ═══════════════════════════════════════════════════════
@user_bp.get("/me")
@jwt_required()
def my_profile():
    """获取当前登录用户的完整资料。

    请求头:
        Authorization: Bearer <access_token>
    返回:
        code: 0, data: {profile: {user_id, nickname, city, vitality, ...}}
    """
    user_id = int(get_jwt_identity())
    profile = get_user_profile(user_id)
    if not profile:
        raise ApiError("用户不存在", 40401, 404)
    return success({"profile": public_user_fields(profile)})


# ═══════════════════════════════════════════════════════
# 更新本人资料
# ═══════════════════════════════════════════════════════
@user_bp.put("/me")
@jwt_required()
def edit_my_profile():
    """更新当前登录用户的资料。

    仅更新白名单内的字段，忽略未知字段。
    支持字段：nickname, avatar_url, gender, birth_year, city, district, bio, interests, real_name
    请求体: 想更新的字段键值对
    请求头: Authorization: Bearer <access_token>
    返回: code: 0, data: {profile}
    """
    data = _json()
    allowed = {"nickname", "avatar_url", "gender", "birth_year", "city",
               "district", "bio", "interests", "real_name"}
    payload = {k: data[k] for k in allowed if k in data}
    if not payload:
        raise ApiError("没有可更新的资料字段")
    user_id = int(get_jwt_identity())
    update_profile(user_id, payload)
    updated = get_user_profile(user_id)
    return success({"profile": public_user_fields(updated)}, "资料已更新")


@user_bp.patch("/me")
@jwt_required()
def patch_my_profile():
    """PATCH 方式更新资料，行为同 PUT /me。"""
    return edit_my_profile()


# ═══════════════════════════════════════════════════════
# 查看他人公开资料
# ═══════════════════════════════════════════════════════
@user_bp.get("/<int:user_id>/public")
def public_profile(user_id: int):
    """查询其他用户的公开资料（无需登录）。

    公开资料不包含手机号、隐私设置等敏感字段。
    URL 参数:
        user_id (int): 目标用户 ID
    返回:
        code: 0, data: {profile: {nickname, avatar_url, vitality, ...}}
    """
    row = get_user_profile(user_id)
    if not row:
        raise ApiError("用户不存在", 40401, 404)
    profile = public_user_fields(row)
    profile.pop("phone", None)
    return success({"profile": profile})
