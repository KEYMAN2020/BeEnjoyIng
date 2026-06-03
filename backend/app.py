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

from activities_routes import activities_bp
app.register_blueprint(activities_bp, url_prefix="/api/v1/activities")

from chat_routes import chat_bp
app.register_blueprint(chat_bp, url_prefix="/api/v1/chat")

from captain_routes import captain_bp
app.register_blueprint(captain_bp, url_prefix="/api/v1/captain")

from partner_routes import partner_bp
app.register_blueprint(partner_bp, url_prefix="/api/v1/partner")

from payment_routes import payment_bp
app.register_blueprint(payment_bp, url_prefix="/api/v1/payment")

from health_routes import health_bp
app.register_blueprint(health_bp, url_prefix="/api/v1/health")

from notification_routes import notification_bp
app.register_blueprint(notification_bp, url_prefix="/api/v1/notifications")

from system_routes import system_bp
app.register_blueprint(system_bp, url_prefix="/api/v1/system")

from system_routes import regions_bp
app.register_blueprint(regions_bp, url_prefix="/api/v1/regions")


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
