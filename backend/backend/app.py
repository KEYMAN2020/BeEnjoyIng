"""Flask 应用入口 — BeEnjoyIng API

集成：CORS / Swagger / Sentry / 限流 / 结构化日志 / 文件上传 / 增强健康检查
"""

import os
from flask import Flask, jsonify, send_from_directory, request, make_response
from flask_cors import CORS
from flasgger import Swagger

from response import ApiError
from db import close_connection, get_connection
from config import active_config as Config
from logger import log

app = Flask(__name__)
app.config.from_object(Config)

# ── Sentry 错误监控 ────────────────────────────────────
if Config.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
    )
    log.info("Sentry 已初始化", dsn_prefix=Config.SENTRY_DSN[:20])

# ── CORS 跨域 ──────────────────────────────────────────
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Swagger API 文档 ───────────────────────────────────
swagger = Swagger(app, template=Config.SWAGGER)

# ── 限流 ───────────────────────────────────────────────
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    enabled=getattr(Config, "RATELIMIT_ENABLED", True),
)


# ── 注册 Blueprint ─────────────────────────────────────

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


# ── 上传 API ────────────────────────────────────────────
from upload_helper import save_uploaded_file


@app.post("/api/v1/upload")
@limiter.limit(Config.RATELIMIT_UPLOAD)
def upload_file():
    """上传文件（图片/语音）

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
      - in: formData
        name: subdir
        type: string
        required: false
    responses:
      200: {description: 上传成功}
      400: {description: 文件错误}
    """
    file = request.files.get("file")
    subdir = request.form.get("subdir", "uploads")
    if not file:
        return jsonify({"code": 400, "data": None, "message": "请选择文件"}), 400

    try:
        url = save_uploaded_file(file, subdir=subdir)
        log.info("文件上传", filename=file.filename, subdir=subdir, url=url)
        return jsonify({"code": 0, "data": {"url": url, "filename": file.filename}, "message": "上传成功"})
    except ValueError as e:
        return jsonify({"code": 400, "data": None, "message": str(e)}), 400


@app.post("/api/v1/upload/multiple")
@limiter.limit(Config.RATELIMIT_UPLOAD)
def upload_multiple():
    """批量上传文件

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
    responses:
      200: {description: 上传成功}
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

    log.info("批量上传", count=len(urls), subdir=subdir)
    return jsonify({
        "code": 0,
        "data": {"urls": urls, "count": len(urls)},
        "message": f"成功上传 {len(urls)} 个文件",
    })


# ── 前端 SPA 静态托管 ──────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend_dist")


@app.route("/")
def frontend_index():
    """SPA 入口页"""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            resp = make_response(f.read(), 200)
            resp.headers["Content-Type"] = "text/html; charset=utf-8"
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp
    return jsonify({"message": "前端未构建"}), 200


@app.route("/assets/<path:filename>")
def frontend_assets(filename):
    """前端静态资源"""
    asset_path = os.path.join(FRONTEND_DIST, "assets", filename)
    if os.path.isfile(asset_path):
        with open(asset_path, encoding="utf-8") as f:
            content = f.read()
        ct = "text/css; charset=utf-8" if filename.endswith(".css") else "application/javascript; charset=utf-8"
        return content, 200, {"Content-Type": ct, "Cache-Control": "public, max-age=31536000"}
    return jsonify({"error": "not found"}), 404


@app.route("/<path:path>")
def frontend_spa_fallback(path):
    """SPA 路由回退 — 非 API 路径返回 index.html"""
    if path.startswith("api/") or path.startswith("apidocs/") or path.startswith("uploads/"):
        return jsonify({"error": "not found"}), 404
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            resp = make_response(f.read(), 200)
            resp.headers["Content-Type"] = "text/html; charset=utf-8"
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp
    return jsonify({"error": "not found"}), 404


# ── 增强健康检查 ───────────────────────────────────────
# 注意：健康检查端点已移至 /api/v1/health，避免与前端 /health 页面冲突
# 通过 health_routes blueprint 注册：app.register_blueprint(health_bp, url_prefix="/api/v1/health")


# ── 错误处理 ─────────────────────────────────────────────

@app.errorhandler(ApiError)
def handle_api_error(error: ApiError):
    log.warning("业务异常", message=error.message, status=error.status_code)
    return error.to_response()


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"code": 404, "data": None, "message": "接口不存在"}), 404


@app.errorhandler(429)
def ratelimit_handler(_e):
    """限流触发处理"""
    log.warning("限流触发", ip=request.remote_addr, path=request.path)
    return jsonify({"code": 429, "data": None, "message": "请求过于频繁，请稍后再试"}), 429


@app.errorhandler(500)
def server_error(e):
    log.error("服务器内部错误", exc_info=True)
    if Config.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except Exception:
            pass
    return jsonify({"code": 500, "data": None, "message": "服务器内部错误"}), 500


# ── 请求生命周期 ─────────────────────────────────────────

@app.before_request
def log_request():
    """记录请求日志"""
    if request.path.startswith("/api/"):
        log.info("请求", method=request.method, path=request.path, ip=request.remote_addr)


@app.teardown_appcontext
def shutdown_db_session(_exception=None):
    close_connection()


if __name__ == "__main__":
    log.info("BeEnjoyIng API 启动", env=os.getenv("FLASK_ENV", "development"), port=5000)
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
