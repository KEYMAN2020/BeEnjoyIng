"""应用配置 — 支持多环境分离"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 从 config.py 所在目录向上查找 .env 文件
_env_path = Path(__file__).resolve().parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parent.parent / ".env"  # backend/backend/→backend/
load_dotenv(dotenv_path=_env_path, override=True)


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv("SECRET_KEY", "be-enjoying-secret-key-2026-32bytes!")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "be-enjoying-jwt-secret-32bytes!")

    # MySQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Vitality2026!")
    DB_NAME = os.getenv("DB_NAME", "silver_vitality")
    DB_CHARSET = "utf8mb4"

    JSON_AS_ASCII = False

    # 验证码
    SMS_CODE_EXPIRE = 300

    # 文件上传
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "mp3", "wav", "ogg", "amr"}

    # 高德地图 Web API
    AMAP_KEY = os.getenv("AMAP_KEY", "4cae03e0ef24554110c6055673d122e0")

    # Swagger
    SWAGGER = {
        "title": "BeEnjoyIng API",
        "description": "中老年社交活动平台后端接口",
        "version": "1.0.0",
        "termsOfService": "",
        "hide_top_text": True,
    }

    # Sentry
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")

    # 限流
    RATELIMIT_DEFAULT = "200/hour"
    RATELIMIT_AUTH = "10/minute"      # 认证接口限流
    RATELIMIT_UPLOAD = "30/minute"    # 上传限流


class DevelopmentConfig(Config):
    """开发环境"""
    DEBUG = True
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    """测试环境"""
    TESTING = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """生产环境"""
    DEBUG = False
    RATELIMIT_ENABLED = True


# 根据环境变量选择配置
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

active_config = config_map.get(os.getenv("FLASK_ENV", "development"), DevelopmentConfig)
