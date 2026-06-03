"""Flask 应用入口 — BeEnjoyIng API

注册所有 Blueprint，提供 /health 健康检查端点。
"""

from flask import Flask, jsonify

from response import ApiError
from db import close_connection

app = Flask(__name__)


# ── 注册 Blueprint ──────────────────────────────────────

from auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

from user_routes import users_bp
app.register_blueprint(users_bp, url_prefix="/api/v1/users")


# ── 健康检查 ─────────────────────────────────────────────

@app.get("/health")
def health():
    """健康检查端点"""
    return jsonify({"status": "ok"})


# ── 错误处理 ─────────────────────────────────────────────

@app.errorhandler(ApiError)
def handle_api_error(error: ApiError):
    return error.to_response()


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"code": 404, "data": None, "message": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(_e):
    return jsonify({"code": 500, "data": None, "message": "服务器内部错误"}), 500


# ── 请求生命周期 ─────────────────────────────────────────

@app.teardown_appcontext
def shutdown_db_session(_exception=None):
    """请求结束后关闭数据库连接"""
    close_connection()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
