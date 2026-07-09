"""文件上传工具 — 本地存储

用法:
  from upload_helper import save_uploaded_file
  url = save_uploaded_file(request.files["file"], subdir="avatars")

支持的文件类型:
  图片: jpg, jpeg, png, gif, webp
  语音: mp3, wav, ogg, amr
"""

import os
import uuid
import time
from config import Config
from response import error

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_VOICE_EXT = {".mp3", ".wav", ".ogg", ".amr"}
ALLOWED_EXT = ALLOWED_IMAGE_EXT | ALLOWED_VOICE_EXT
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _ensure_dir(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def _ext(filename: str) -> str:
    """获取文件扩展名（小写）"""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def save_uploaded_file(file_storage, subdir: str = "uploads") -> str:
    """保存上传文件，返回可公开访问的 URL

    参数:
        file_storage: request.files["xxx"]
        subdir: 子目录名（avatars / albums / site_photos / voice）

    返回:
        文件 URL 字符串，如 /uploads/avatars/uuid.jpg

    抛出:
        ApiError 400 — 文件类型不允许 / 文件过大 / 无文件
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("未提供文件")

    ext = _ext(file_storage.filename)
    if ext not in ALLOWED_EXT:
        raise ValueError(f"不支持的文件类型: {ext}")

    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex}{ext}"
    relative_path = f"uploads/{subdir}/{unique_name}"

    upload_dir = os.path.join(Config.UPLOAD_FOLDER, subdir)
    _ensure_dir(upload_dir)

    abs_path = os.path.join(Config.UPLOAD_FOLDER, relative_path)
    file_storage.save(abs_path)

    # 返回相对 URL（Flask 通过 static 或自定义路由提供）
    return f"/{relative_path}"


def save_base64_image(base64_str: str, subdir: str = "uploads") -> str:
    """保存 base64 编码的图片

    参数:
        base64_str: "data:image/png;base64,iVBOR..." 或纯 base64
        subdir: 子目录

    返回:
        文件 URL 字符串
    """
    import base64

    if base64_str.startswith("data:image/"):
        # 提取格式和 base64 数据
        header, _, b64_data = base64_str.partition(",")
        ext_map = {
            "/png": ".png", "/jpeg": ".jpg", "/jpg": ".jpg",
            "/gif": ".gif", "/webp": ".webp",
        }
        ext = ".jpg"
        for key, value in ext_map.items():
            if key in header:
                ext = value
                break
        b64_data = b64_data.strip()
    else:
        b64_data = base64_str
        ext = ".jpg"

    try:
        file_data = base64.b64decode(b64_data)
    except Exception:
        raise ValueError("Base64 解码失败")

    if len(file_data) > MAX_FILE_SIZE:
        raise ValueError("文件过大，最大 10MB")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    relative_path = f"uploads/{subdir}/{unique_name}"

    upload_dir = os.path.join(Config.UPLOAD_FOLDER, subdir)
    _ensure_dir(upload_dir)

    abs_path = os.path.join(Config.UPLOAD_FOLDER, relative_path)
    with open(abs_path, "wb") as f:
        f.write(file_data)

    return f"/{relative_path}"
