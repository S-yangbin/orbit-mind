"""
时区工具模块
统一使用北京时间 (UTC+8)
"""

from datetime import datetime, timezone, timedelta


# 北京时间时区
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)
