# -*- coding: utf-8 -*-
"""
银发活力平台 — 配置模块
========================
集中管理应用配置，所有配置项支持环境变量覆盖。
"""

import os
from datetime import timedelta


class Config:
    """应用配置。

    数据库、JWT、密钥等配置项集中在此，
    生产部署时建议通过环境变量注入敏感信息，避免硬编码。
    """

    # ── Flask / JWT 密钥 ──
    # SECRET_KEY 用于 Flask session 签名
    SECRET_KEY = os.getenv("SECRET_KEY", "silver-vitality-dev-secret-change-me")
    # JWT_SECRET_KEY 用于 Token 签名，应与 SECRET_KEY 不同
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "silver-vitality-jwt-secret-change-me")
    # Access Token 有效期：2 小时
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    # Refresh Token 有效期：30 天
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ── 数据库 ──
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Vitality2026!")
    DB_NAME = os.getenv("DB_NAME", "silver_vitality")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    # ── 其他 ──
    JSON_AS_ASCII = False
