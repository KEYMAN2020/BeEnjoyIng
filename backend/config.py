"""应用配置"""

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "be-enjoying-secret-key-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "be-enjoying-jwt-secret-2026")

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
