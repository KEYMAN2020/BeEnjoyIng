"""给所有路由函数添加 Swagger 基础文档"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app

# 每个 Blueprint 对应的 tag 名称
TAG_MAP = {
    "auth": "认证",
    "users": "用户",
    "activities": "活动",
    "chat": "聊天",
    "captain": "领队",
    "partner": "合作伙伴",
    "payment": "支付",
    "health": "健康",
    "notifications": "通知",
    "system": "系统",
    "regions": "系统",
}

count = 0
for rule in app.url_map.iter_rules():
    if rule.endpoint == "static":
        continue

    # 找到对应的 tag
    tag = "其他"
    for prefix, t in TAG_MAP.items():
        if rule.rule.startswith(f"/api/v1/{prefix}"):
            tag = t
            break

    # 获取视图函数
    try:
        view_func = app.view_functions[rule.endpoint]
    except KeyError:
        continue

    # 检查是否已有 flasgger docstring（包含 ---）
    doc = view_func.__doc__ or ""
    if "---" in doc:
        print(f"  [已有] {rule.rule}")
        continue

    # 获取端点名称作为摘要
    summary = doc.strip().split("\n")[0] if doc.strip() else rule.endpoint

    # 添加基础 docstring
    new_doc = f"{summary}\n    ---\n    tags:\n      - {tag}\n    "
    view_func.__doc__ = new_doc
    print(f"  [新增] {rule.rule} -> {tag}")
    count += 1

print(f"\n共更新 {count} 个端点")
