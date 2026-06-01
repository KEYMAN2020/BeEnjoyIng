# -*- coding: utf-8 -*-
"""
银发活力平台 — 数据库连接管理
==============================
基于 Flask 应用上下文（g 对象）管理 MySQL 连接。
每个请求生命周期内复用同一连接，请求结束后自动关闭。

依赖 PyMySQL（同步驱动，配置简单，适合当前 MVP 阶段）。
生产环境可考虑替换为连接池方案（如 DBUtils / SQLAlchemy）。
"""

import pymysql
from flask import current_app, g


def get_db():
    """获取当前请求的数据库连接（惰性初始化）。

    连接参数从 Flask 配置读取（config.py），
    使用 DictCursor 便于按字段名访问查询结果。
    Returns:
        pymysql.Connection
    """
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset=current_app.config["DB_CHARSET"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return g.db


def close_db(_exc=None):
    """关闭当前请求的数据库连接（在 teardown 中调用）。"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_one(sql, params=None):
    """执行查询，返回单行结果。

    Args:
        sql: SQL 查询语句（使用 %s 占位符）
        params: 参数元组
    Returns:
        dict | None — 查询结果行，无结果返回 None
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def query_all(sql, params=None):
    """执行查询，返回所有结果行。

    Args:
        sql: SQL 查询语句（使用 %s 占位符）
        params: 参数元组
    Returns:
        list[dict] — 结果行列表，无结果返回空列表
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def execute(sql, params=None):
    """执行 INSERT / UPDATE / DELETE 操作。

    Args:
        sql: SQL 语句（使用 %s 占位符）
        params: 参数元组
    Returns:
        tuple: (lastrowid, rowcount)
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.lastrowid, cursor.rowcount


def commit():
    """提交当前事务。"""
    get_db().commit()


def rollback():
    """回滚当前事务。"""
    get_db().rollback()
