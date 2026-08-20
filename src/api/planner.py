"""
推送计划预览 API
计算指定日期内所有消息规则的触发时间
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any
from croniter import croniter

from src.core import config_manager as cm

router = APIRouter(prefix="/api/planner", tags=["Planner"])


def get_trigger_times_for_date(cron_expr: str, target_date: date) -> List[datetime]:
    """
    计算指定 Cron 表达式在目标日期内的所有触发时间

    Args:
        cron_expr: Cron 表达式（如 "0 8 * * *"）
        target_date: 目标日期

    Returns:
        该日期内所有触发时间的 datetime 列表
    """
    base = datetime.combine(target_date, time.min)
    end = datetime.combine(target_date, time.max)

    # 从前一天开始迭代，确保捕获当天的所有触发点
    start = base - timedelta(days=1)
    iter = croniter(cron_expr, start)

    times = []
    while True:
        next_time = iter.get_next(datetime)
        if next_time > end:
            break
        if next_time >= base:
            times.append(next_time)
    return times


@router.get("/daily")
async def preview_daily_plan(target_date: str = None) -> Dict[str, Any]:
    """
    预览指定日期的推送计划

    Args:
        target_date: 目标日期（格式: YYYY-MM-DD），不传则默认为明天
    """
    # 1. 解析日期
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
    else:
        target_date = datetime.now().date() + timedelta(days=1)

    # 2. 加载配置
    config = cm.load_config()
    channels = {ch.name: ch for ch in config.channels}

    # 3. 遍历所有启用的消息规则
    events = []
    for rule in config.messages:
        if not rule.enabled:
            continue

        # 获取渠道名称列表
        channel_names = rule.channels or []
        if not channel_names:
            continue

        # 计算触发时间
        try:
            trigger_times = get_trigger_times_for_date(rule.original_schedule, target_date)
        except Exception as e:
            # Cron 表达式无效时跳过
            continue

        if not trigger_times:
            continue

        # 获取标题（从 data 中提取）
        title = rule.data.get("title", rule.id)

        for trigger_time in trigger_times:
            events.append({
                "time": trigger_time.strftime("%H:%M"),
                "datetime": trigger_time.isoformat(),
                "rule_id": rule.id,
                "description": rule.description or rule.id,
                "channels": channel_names,
                "title": title,
                "cron": rule.original_schedule
            })

    # 4. 按时间排序
    events.sort(key=lambda x: x["time"])

    # 5. 统计信息
    total_count = len(events)
    channel_stats = {}
    for event in events:
        for ch in event["channels"]:
            channel_stats[ch] = channel_stats.get(ch, 0) + 1

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "date": target_date.isoformat(),
            "total": total_count,
            "events": events,
            "channel_stats": channel_stats
        }
    }