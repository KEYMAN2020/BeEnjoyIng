"""MySQL 数据库连接管理器（PyMySQL + 线程本地存储）"""

import pymysql
import pymysql.cursors
import threading
from config import Config

_local = threading.local()


def get_connection():
    """获取当前线程的数据库连接（懒加载）"""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset=Config.DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return _local.conn


def close_connection():
    """关闭当前线程的数据库连接"""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None


def execute_query(sql: str, params: tuple | None = None) -> list[dict]:
    """执行 SELECT 查询，返回字典列表"""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def execute_query_one(sql: str, params: tuple | None = None) -> dict | None:
    """执行 SELECT 查询，返回单条记录"""
    rows = execute_query(sql, params)
    return rows[0] if rows else None


def execute_insert(sql: str, params: tuple | None = None) -> int:
    """执行 INSERT 语句，返回自增 ID"""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid


def execute_update(sql: str, params: tuple | None = None) -> int:
    """执行 UPDATE/DELETE 语句，返回影响行数"""
    conn = get_connection()
    with conn.cursor() as cursor:
        affected = cursor.execute(sql, params or ())
        conn.commit()
        return affected
