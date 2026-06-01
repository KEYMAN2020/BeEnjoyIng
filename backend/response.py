# -*- coding: utf-8 -*-
"""
银发活力平台 — 统一响应格式
============================
定义 API 统一 JSON 响应结构和业务异常类。

成功响应格式：{"code": 0,     "data": {...}, "message": "ok"}
错误响应格式：{"code": 40001, "message": "错误描述", "data": null}
"""

from flask import jsonify


OK_MESSAGE = "ok"


class ApiError(Exception):
    """业务异常，携带错误码、HTTP 状态码和可选 data。

    用法：
        raise ApiError("手机号格式错误")                          # → 400
        raise ApiError("手机号或密码错误", http_status=401)        # → 401
        raise ApiError("用户不存在", 40401, 404)                   # → 404

    Attributes:
        message (str):     用户可读的错误描述
        code (int):        业务错误码（非 0 表示错误）
        http_status (int): HTTP 状态码
        data (any):        附加数据
    """

    def __init__(self, message, code=40001, http_status=400, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.data = data

    def to_response(self):
        """将异常序列化为统一 JSON 响应。"""
        return jsonify({
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }), self.http_status


def success(data=None, message=OK_MESSAGE, http_status=200):
    """成功响应。

    Args:
        data: 响应数据，默认空 dict
        message: 成功消息
        http_status: HTTP 状态码
    Returns:
        (Response, int) — Flask 可直接返回的元组
    """
    return jsonify({"code": 0, "data": data or {}, "message": message}), http_status


def error(message, code=40001, http_status=400, data=None):
    """错误响应。

    Args:
        message: 错误描述
        code: 业务错误码
        http_status: HTTP 状态码
        data: 附加数据
    Returns:
        (Response, int)
    """
    return jsonify({"code": code, "message": message, "data": data}), http_status


# 兼容别名（部分路由导入 json_success / json_error）
json_success = success
json_error = error
