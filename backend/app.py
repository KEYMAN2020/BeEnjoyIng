"""BeEnjoyIng 后端入口

按规格表逐接口开发，当前仅包含 API #1 send-code。
"""

import os
from flask import Flask
from response import ApiError
from auth_routes import auth_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

    # ── 健康检查 ──
    @app.get("/health")
    def health():
        return {"code": 0, "data": {"status": "healthy"}, "message": "ok"}

    # ── 全局错误处理 ──
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return err.to_response()

    @app.errorhandler(404)
    def not_found(_):
        return {"code": 404, "data": None, "message": "接口不存在"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return {"code": 405, "data": None, "message": "方法不允许"}, 405

    @app.errorhandler(Exception)
    def internal_error(err):
        app.logger.exception("Unhandled exception: %s", err)
        return {"code": 500, "data": None, "message": "服务器内部错误"}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
