"""JWT 认证装饰器 — 从 Authorization header 提取当前用户"""

from functools import wraps
from flask import request, g
from jwt_helper import decode_token
from response import error


def require_auth(f):
    """要求用户已登录的装饰器，解码 JWT 存入 g.current_user"""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("未提供认证令牌", 401)

        token = auth_header[len("Bearer "):]
        payload = decode_token(token)
        if payload is None:
            return error("令牌无效或已过期", 401)

        g.current_user = payload
        return f(*args, **kwargs)

    return decorated
