"""操作日志 — 写入 operation_logs 表"""

from db import execute_insert


def log_operation(
    operator_id: int,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> int:
    """记录一条操作日志，返回日志 ID"""
    sql = """INSERT INTO operation_logs
             (operator_id, action, target_type, target_id, detail, ip_address, created_at)
             VALUES (%s, %s, %s, %s, %s, %s, NOW())"""
    return execute_insert(sql, (operator_id, action, target_type, target_id, detail, ip_address))
