"""Flask 应用入口 — BeEnjoyIng API

注册所有 Blueprint，提供 /health 健康检查端点、Swagger 文档、文件上传。
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flasgger import Swagger

from response import ApiError
from db import close_connection
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# ── CORS（跨域） ────────────────────────────────────────
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Swagger API 文档 ────────────────────────────────────
swagger = Swagger(app, template=Config.SWAGGER)


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


# ── 文件上传服务 ────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """提供上传文件的静态访问"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# ── 上传 API（通用文件上传） ─────────────────────────────
from flask import request
from upload_helper import save_uploaded_file, ALLOWED_IMAGE_EXT

@app.post("/api/v1/upload")
def upload_file():
    """上传文件（图片/语音）

    请求: multipart/form-data, field="file"
    响应: {"code": 0, "data": {"url": "/uploads/...", "filename": "xxx.jpg"}}
    ---
    tags:
      - 文件上传
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: 上传的文件（图片或语音）
      - in: formData
        name: subdir
        type: string
        required: false
        description: 子目录（avatars/albums/site_photos/voice）
    responses:
      200:
        description: 上传成功
    """
    file = request.files.get("file")
    subdir = request.form.get("subdir", "uploads")

    if not file:
        return jsonify({"code": 400, "data": None, "message": "请选择文件"}), 400

    try:
        url = save_uploaded_file(file, subdir=subdir)
        return jsonify({
            "code": 0,
            "data": {"url": url, "filename": file.filename},
            "message": "上传成功",
        })
    except ValueError as e:
        return jsonify({"code": 400, "data": None, "message": str(e)}), 400


# ── 批量上传 ─────────────────────────────────────────────
@app.post("/api/v1/upload/multiple")
def upload_multiple():
    """批量上传文件

    请求: multipart/form-data, field="files[]" (多个文件)
    响应: {"code": 0, "data": {"urls": ["/uploads/...", ...]}}
    ---
    tags:
      - 文件上传
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: files[]
        type: array
        items: {type: file}
        required: true
        description: 多个文件
    responses:
      200:
        description: 上传成功
    """
    files = request.files.getlist("files[]")
    subdir = request.form.get("subdir", "uploads")

    if not files:
        return jsonify({"code": 400, "data": None, "message": "请选择文件"}), 400

    urls = []
    for file in files:
        try:
            url = save_uploaded_file(file, subdir=subdir)
            urls.append(url)
        except ValueError:
            continue

    return jsonify({
        "code": 0,
        "data": {"urls": urls, "count": len(urls)},
        "message": f"成功上传 {len(urls)} 个文件",
    })


# ── 健康检查 ─────────────────────────────────────────────

@app.get("/health")
def health():
    """健康检查端点

    ---
    tags:
      - 系统
    responses:
      200:
        description: 服务正常
    """
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
