"""系统模块路由 — 3 个 API 端点

路由前缀: /api/v1/system, /api/v1/regions
"""

from flask import Blueprint, request
from response import success, error
from db import execute_query, execute_query_one

system_bp = Blueprint("system", __name__)
regions_bp = Blueprint("regions", __name__)


# ═══════════════════════════════════════════════════════
# 1. 获取系统配置
# ═══════════════════════════════════════════════════════
@system_bp.get("/config/<key>")
def get_config(key):
    """获取系统配置项
    ---
    tags:
      - 系统
    parameters:
      - name: key
        in: path
        type: string
        required: true
        description: 配置键名
    responses:
      200:
        description: 配置值
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                config:
                  type: object
                  properties:
                    key: {type: string}
                    value: {type: string}
                    group: {type: string}
                    description: {type: string}
            message: {type: string, example: ok}
      404: {description: 配置项不存在}
    """
    config = execute_query_one(
        "SELECT * FROM system_config WHERE config_key = %s",
        (key,),
    )
    if not config:
        return error("配置项不存在", 404)

    return success({
        "config": {
            "key": config["config_key"],
            "value": config["config_value"],
            "group": config.get("config_group", "general"),
            "description": config.get("description", ""),
        }
    })


# ═══════════════════════════════════════════════════════
# 2. 获取地区列表
# ═══════════════════════════════════════════════════════
@regions_bp.get("")
def list_regions():
    """获取地区列表（省/市/区三级）
    ---
    tags:
      - 系统
    parameters:
      - name: parent_code
        in: query
        type: string
        required: false
        description: 上级行政编码，为空返回所有省份
      - name: level
        in: query
        type: integer
        required: false
        description: 层级（1=省/2=市/3=区）
    responses:
      200:
        description: 地区列表
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                regions:
                  type: array
                  items:
                    type: object
                    properties:
                      code: {type: string}
                      name: {type: string}
                      parent_code: {type: string}
                      level: {type: integer}
                      pinyin: {type: string}
                      short_name: {type: string}
            message: {type: string, example: ok}
    """
    parent_code = request.args.get("parent_code", "")
    level = request.args.get("level", type=int)

    conditions = ["r.is_active = 1"]
    params = []

    if parent_code:
        conditions.append("r.parent_code = %s")
        params.append(parent_code)
    if level is not None:
        conditions.append("r.level = %s")
        params.append(level)

    where = " AND ".join(conditions) if conditions else "1=1"

    rows = execute_query(
        f"SELECT * FROM regions r WHERE {where} ORDER BY r.code ASC",
        params,
    )

    return success({
        "regions": [{
            "code": r["code"],
            "name": r["name"],
            "parent_code": r.get("parent_code"),
            "level": r["level"],
            "pinyin": r.get("pinyin", ""),
            "short_name": r.get("short_name", ""),
        } for r in rows]
    })
