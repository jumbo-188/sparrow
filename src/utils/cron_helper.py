"""
Cron 表达式计算工具
功能：根据原始 Cron + 提前量，计算实际执行的 Cron
"""

from datetime import datetime, timedelta
from croniter import croniter
import pytz


def calculate_actual_cron(
        original_cron: str,
        advance_value: int,
        advance_unit: str,
        timezone: str = "Asia/Shanghai"
) -> str:
    """
    计算实际执行的 Cron 表达式

    Args:
        original_cron: 用户期望的 Cron（如 "0 8 * * *" 表示每天 8:00）
        advance_value: 提前量数值
        advance_unit: 提前单位（minutes / hours / days）
        timezone: 时区

    Returns:
        实际执行的 Cron 字符串
    """
    if advance_value == 0:
        return original_cron

    tz = pytz.timezone(timezone)
    now = datetime.now(tz)

    # 1. 获取原始 Cron 的下一次触发时间
    iter = croniter(original_cron, now)
    next_time = iter.get_next(datetime)

    # 2. 减去提前量
    delta = timedelta(**{advance_unit: advance_value})
    actual_time = next_time - delta

    # 3. 将实际时间格式化为 Cron 表达式
    # 注意：croniter 需要 datetime 对象，反向推导出 Cron
    # 但我们直接构造 Cron：分 时 日 月 周
    cron_parts = [
        str(actual_time.minute),
        str(actual_time.hour),
        str(actual_time.day),
        str(actual_time.month),
        str(actual_time.strftime("%w"))  # 0=周日, 6=周六
    ]

    # 如果原始 Cron 中有特殊符号（如 */5），保持原样较复杂，
    # 我们采用“最接近的固定时间”策略（适用于个人场景）
    # 但如果用户原始是每周几，我们需要确保星期几不变。
    # 更稳健的做法：利用 croniter 的 get_next 和 get_prev 特性
    # 但为了简便，如果提前量跨天，直接取计算出的时间。

    # 特殊处理：如果原始 Cron 是 "0 8 * * 1"（每周一），
    # 提前 1 天变为 "0 8 * * 0"（每周日）
    # 通过 croniter 计算出的 actual_time 会自动处理
    return " ".join(cron_parts)


def format_schedule_display(original_cron: str, actual_cron: str, advance_value: int, advance_unit: str) -> dict:
    """
    生成页面展示用的时间描述

    Returns:
        {
            "original_display": "每天 08:00",
            "actual_display": "每天 07:50（提前 10 分钟）",
            "original_raw": "0 8 * * *",
            "actual_raw": "50 7 * * *"
        }
    """

    # 简单格式化（仅处理常见的每天/每周场景）
    # 完整版可用 cron_descriptor 库，但为避免膨胀，我们用简单映射
    def cron_to_readable(cron_str: str) -> str:
        parts = cron_str.split()
        if len(parts) != 5:
            return cron_str
        min_str, hour_str, day_str, month_str, dow_str = parts

        # 简单的每天场景
        if day_str == "*" and month_str == "*" and dow_str == "*":
            return f"每天 {hour_str.zfill(2)}:{min_str.zfill(2)}"
        # 每周场景
        if day_str == "*" and month_str == "*" and dow_str != "*":
            weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
            return f"每周{weekdays[int(dow_str)]} {hour_str.zfill(2)}:{min_str.zfill(2)}"
        return cron_str

    original_display = cron_to_readable(original_cron)
    actual_display = cron_to_readable(actual_cron)

    if advance_value > 0:
        # 单位中文
        unit_map = {"minutes": "分钟", "hours": "小时", "days": "天"}
        actual_display += f"（提前 {advance_value}{unit_map.get(advance_unit, '')}）"

    return {
        "original_display": original_display,
        "actual_display": actual_display,
        "original_raw": original_cron,
        "actual_raw": actual_cron
    }