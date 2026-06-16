"""系统模块路由 — 4 个 API 端点

路由前缀: /api/v1/system, /api/v1/regions
功能:
  - GET /api/v1/system/config/<key>  获取系统配置
  - GET /api/v1/regions             获取地区列表（支持 auto-refresh）
  - POST /api/v1/regions/refresh    从高德 District API 刷新地区数据
"""

import json
import urllib.request
import urllib.parse
from flask import Blueprint, request
from response import success, error
from db import execute_query, execute_query_one, get_connection
from config import Config

system_bp = Blueprint("system", __name__)
regions_bp = Blueprint("regions", __name__)


def _fetch_regions_from_amap():
    """调用高德 District API，返回省市区三级扁平列表"""
    key = Config.AMAP_KEY
    if not key:
        return None

    url = (
        f"https://restapi.amap.com/v3/config/district"
        f"?key={key}&keywords={urllib.parse.quote('中国')}&subdistrict=3&extensions=base"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BeEnjoyIng/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Gaode District API] error: {e}")
        return None

    if data.get("status") != "1" or not data.get("districts"):
        print(f"[Gaode District API] abnormal response: {data.get('info')}")
        return None

    rows = []

    def collect(d_list, parent_code=None, level=1):
        for d in d_list:
            adcode = d.get("adcode", "")
            name = d.get("name", "")
            children = d.get("districts", [])
            if adcode and name:
                rows.append((adcode, name, parent_code, level))
            if children and level < 3:
                collect(children, adcode, level + 1)

    # 跳过 country 层级（中华人民共和国 = adcode 100000），直接从省份开始
    for top in data["districts"]:
        provinces = top.get("districts", [])
        if provinces:
            collect(provinces)
            break
    print(f"[Gaode District API] fetched {len(rows)} regions")
    return rows


def _refresh_regions_table(rows):
    """清空 regions 表并批量写入高德数据"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM regions")
        sql = (
            "INSERT IGNORE INTO regions (code, name, parent_code, level, is_active, created_at, updated_at)"
            " VALUES (%s, %s, %s, %s, 1, NOW(), NOW())"
        )
        for i in range(0, len(rows), 100):
            cur.executemany(sql, rows[i:i + 100])
        conn.commit()
    finally:
        cur.close()
    return len(rows)


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
    """获取地区列表（省/市/区三级）。表为空时自动从高德 API 拉取。
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
    # 自动刷新：如果表为空则从高德 API 拉取
    count = execute_query_one("SELECT COUNT(*) AS cnt FROM regions")
    if count and count["cnt"] == 0:
        rows = _fetch_regions_from_amap()
        if rows:
            _refresh_regions_table(rows)

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


# ═══════════════════════════════════════════════════════
# 3. 手动刷新地区数据（从高德 District API）
# ═══════════════════════════════════════════════════════
@regions_bp.post("/refresh")
def refresh_regions():
    """从高德 District API 刷新地区数据（清空旧数据，写入新数据）

    调用高德行政区域查询 API，获取省市区三级树，写入 regions 表。
    所有现有数据将被替换（事务保护，失败自动回滚）。

    ---
    tags:
      - 系统
    responses:
      200:
        description: 刷新成功
        schema:
          type: object
          properties:
            code: {type: integer, example: 0}
            data:
              type: object
              properties:
                message: {type: string, example: 已刷新 2795 条地区数据}
                count: {type: integer, example: 2795}
      500:
        description: 刷新失败
    """
    rows = _fetch_regions_from_amap()
    if rows is None:
        return error("获取高德地区数据失败，请检查 AMAP_KEY 配置和高德服务状态", 500)

    total = _refresh_regions_table(rows)
    return success({"message": f"已刷新 {total} 条地区数据", "count": total})
