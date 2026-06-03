"""应用配置"""

import os


class Config:
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

    # 验证码有效期（秒）
    SMS_CODE_EXPIRE = 300

    # 文件上传
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "mp3", "wav", "ogg", "amr"}

    # Swagger
    SWAGGER = {
        "title": "BeEnjoyIng API",
        "description": "中老年社交活动平台后端接口",
        "version": "1.0.0",
        "termsOfService": "",
        "hide_top_text": True,
    }
