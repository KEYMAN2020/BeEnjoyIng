"""Flask 应用入口 — BeEnjoyIng API

注册所有 Blueprint，提供 /health 健康检查端点。
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify

# Allow importing the shared structured logger from ../references/logger.py
ROOT_DIR = Path(__file__).resolve().parent.parent
REFERENCES_DIR = ROOT_DIR / "references"
if str(REFERENCES_DIR) not in sys.path:
    sys.path.insert(0, str(REFERENCES_DIR))

from logger import init_logger  # noqa: E402

from response import ApiError  # noqa: E402
from db import close_connection  # noqa: E402

PROJECT_ID = "proj_20260602_2340"

app = Flask(__name__)
slog = init_logger(PROJECT_ID)


# ── 注册 Blueprint ──────────────────────────────────────

from auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")


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
