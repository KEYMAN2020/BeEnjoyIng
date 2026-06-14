"""JWT 令牌生成与验证

依赖 PyJWT（Flask-JWT-Extended 的传递依赖）
"""

import time
import jwt
from config import Config

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 1800       # 30 分钟
REFRESH_TOKEN_EXPIRE = 604800    # 7 天


def generate_access_token(user_id: int, role: str = "user") -> str:
    """生成访问令牌"""
    payload = {
        "user_id": user_id,
        "role": role,
        "type": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """生成刷新令牌"""
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": int(time.time()),
        "exp": int(time.time()) + REFRESH_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码并验证 JWT，失败返回 None"""
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
