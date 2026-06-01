# -*- coding: utf-8 -*-
"""
银发活力平台 — 用户认证模块入口
==============================
Flask 应用工厂，负责：
  - 加载配置
  - 初始化 JWT
  - 注册蓝图（认证 + 用户资料）
  - 注册全局错误处理器
  - 注册数据库连接清理
"""

from flask import Flask
from flask_jwt_extended import JWTManager

from config import Config
from auth_routes import auth_bp
from user_routes import user_bp
from response import success, ApiError
from db import close_db


def create_app() -> Flask:
    """创建并配置 Flask 应用实例。

    Returns:
        Flask: 配置完成的应用实例
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json.ensure_ascii = False

    # ── JWT 认证初始化 ──
    JWTManager(app)

    # ── 蓝图注册（url_prefix 统一在此处声明，蓝图中不重复） ──
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(user_bp, url_prefix="/api/v1/users")

    # ── 请求结束自动关闭数据库连接 ──
    app.teardown_appcontext(close_db)

    # ── 健康检查 ──
    @app.get("/health")
    def health_check():
        """健康检查接口，用于 Docker / 负载均衡探活。"""
        return success({"status": "healthy", "service": "silver-vitality-auth"})

    # ── 全局错误处理器 ──
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        """业务异常统一处理，返回结构化 JSON 错误。"""
        return err.to_response()

    @app.errorhandler(404)
    def not_found(_):
        """未匹配路由 → 404。"""
        return {"code": 40404, "message": "接口不存在", "data": None}, 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        """请求方法不允许 → 405。"""
        return {"code": 40500, "message": "请求方法不允许", "data": None}, 405

    @app.errorhandler(Exception)
    def internal_error(err):
        """未捕获异常兜底，返回通用 500，详情写日志。"""
        app.logger.exception("Unhandled exception: %s", err)
        return {"code": 50000, "message": "服务器内部错误", "data": None}, 500

    return app


# ── 全局实例（供 gunicorn / flask run 直接使用） ──
app = create_app()


if __name__ == "__main__":
    import os
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
