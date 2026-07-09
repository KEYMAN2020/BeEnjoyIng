"""结构化日志模块

使用方式:
  from logger import log
  log.info("用户注册", user_id=123, phone="138***")
  log.error("数据库连接失败", exc_info=True)
  log.warning("限流触发", ip=ip, endpoint=endpoint)
"""

import os
import json
import logging
import sys
from datetime import datetime, timezone, timedelta

# 北京时区
CST = timezone(timedelta(hours=8))


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "time": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加异常信息
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        return json.dumps(log_entry, ensure_ascii=False)


def _get_handler():
    """获取日志处理器"""
    env = os.getenv("FLASK_ENV", "development")

    if env == "production":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
    else:
        # 开发环境人类可读
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-7s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    return handler


# 根日志器
logger = logging.getLogger("be-enjoying")
logger.setLevel(logging.INFO)
logger.addHandler(_get_handler())
logger.propagate = False


class LoggerProxy:
    """便捷日志代理，支持 extra 关键字"""

    def _log(self, level: int, msg: str, **extra):
        record = logging.LogRecord(
            name="be-enjoying",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        record.extra = extra
        logger.handle(record)

    def info(self, msg: str, **extra):
        self._log(logging.INFO, msg, **extra)

    def warning(self, msg: str, **extra):
        self._log(logging.WARNING, msg, **extra)

    def error(self, msg: str, **extra):
        self._log(logging.ERROR, msg, **extra)

    def debug(self, msg: str, **extra):
        self._log(logging.DEBUG, msg, **extra)


log = LoggerProxy()
