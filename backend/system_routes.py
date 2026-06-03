"""系统模块路由 — 2 个 API 端点

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
    """获取系统配置项"""
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
    """获取地区列表

    查询参数: parent_code (上级行政编码), level (层级)
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
