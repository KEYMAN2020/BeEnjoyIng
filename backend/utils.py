# -*- coding: utf-8 -*-
"""
银发活力平台 — 工具函数模块
============================
提供认证相关的工具函数：
  - 手机号格式校验
  - bcrypt 密码哈希与校验
  - 验证码生成与校验（Mock，内存存储）
  - JWT Token 签发
  - Token 黑名单管理

注意：当前验证码和黑名单使用进程内存存储，
多实例部署或重启后会丢失。生产环境应替换为 Redis。
"""

import re
import random
import bcrypt
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti


# 中国手机号正则：1 开头，第二位 3-9，共 11 位
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")

# ── 内存存储（MVP 用，生产请替换为 Redis） ──
_verification_codes = {}
token_blacklist = set()


def is_valid_phone(phone: str) -> bool:
    """校验中国手机号格式。

    Args:
        phone: 待校验手机号
    Returns:
        True 表示格式正确
    """
    return bool(phone and PHONE_RE.match(phone))


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希。

    Args:
        password: 明文密码
    Returns:
        bcrypt 哈希字符串
    Raises:
        ValueError: 密码长度不足 6 位
    """
    if not password or len(password) < 6:
        raise ValueError("密码长度不能少于6位")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码与 bcrypt 哈希是否匹配。

    Args:
        password: 明文密码
        password_hash: bcrypt 哈希字符串
    Returns:
        True 表示匹配
    """
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_verification_code(phone: str, purpose: str = "auth") -> str:
    """生成并存储短信验证码（Mock 实现）。

    验证码为 6 位随机数，有效期 5 分钟。
    生产环境中应集成真实短信通道，并用 Redis 替代内存存储。

    Args:
        phone: 目标手机号
        purpose: 验证码用途（如 "auth" / "reset_password"）
    Returns:
        生成的验证码字符串
    """
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    _verification_codes[(phone, purpose)] = {"code": code, "expires_at": expires_at}
    print(f"[Mock SMS] phone={phone}, purpose={purpose}, code={code}, expires_at={expires_at.isoformat()}Z")
    return code


def verify_code(phone: str, code: str, purpose: str = "auth", consume: bool = True) -> bool:
    """校验验证码。

    Args:
        phone: 手机号
        code: 待校验的验证码
        purpose: 验证码用途
        consume: 校验成功后是否立即消耗（删除）
    Returns:
        True 表示验证码正确且未过期
    """
    record = _verification_codes.get((phone, purpose))
    if not record:
        return False
    if datetime.utcnow() > record["expires_at"]:
        _verification_codes.pop((phone, purpose), None)
        return False
    ok = record["code"] == str(code)
    if ok and consume:
        _verification_codes.pop((phone, purpose), None)
    return ok


def issue_tokens(user_id: int):
    """签发 Access Token + Refresh Token 对。

    Args:
        user_id: 用户 ID
    Returns:
        dict: {access_token, refresh_token, token_type, expires_in}
    """
    identity = str(user_id)
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer", "expires_in": 7200}


def blacklist_encoded_token(encoded_token: str):
    """将已编码的 Token 加入黑名单。

    Args:
        encoded_token: JWT 字符串
    """
    if not encoded_token:
        return
    jti = get_jti(encoded_token)
    token_blacklist.add(jti)
