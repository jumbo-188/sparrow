"""
明日推送计划汇总发送器
每天定时发送第二天的推送计划清单
"""

import datetime
import logging
from typing import List, Dict, Any

from src.core import config_manager as cm
from src.core.sender import send_push
from src.api.planner import get_trigger_times_for_date

logger = logging.getLogger(__name__)


def generate_plan_message(target_date: datetime.date, events: List[Dict[str, Any]]) -> str:
    """
    生成推送计划汇总消息（手机端优化版）
    """
    if not events:
        return f"📅 {target_date.strftime('%Y-%m-%d')}\n\n暂无推送任务"

    lines = [
        # f"📅 **{target_date.strftime('%Y-%m-%d')}**",
        f"共 {len(events)} 条",
        "",
        "---"
    ]

    # 按时间分组
    time_groups: Dict[str, List[Dict]] = {}
    for event in events:
        time_key = event.get("time", "未知时间")
        if time_key not in time_groups:
            time_groups[time_key] = []
        time_groups[time_key].append(event)

    # 按时间排序
    for time_key in sorted(time_groups.keys()):
        group_events = time_groups[time_key]
        lines.append(f"**{time_key}**")
        for event in group_events:
            # 简化显示：只显示规则ID和描述（渠道信息省略，因为手机空间有限）
            desc = event.get("description", event.get("rule_id", ""))
            # 去掉过长的描述前缀（如 "工商-", "建行-" 等，在规则ID中已有体现）
            lines.append(f"• {desc}")
        lines.append("")

    lines.append("---")
    lines.append(f"🕊️ Sparrow 自动推送 · {datetime.datetime.now().strftime('%H:%M')} ")

    return "\n".join(lines)


async def send_daily_plan():
    """
    发送明日推送计划汇总
    由调度器每天定时调用
    """
    logger.info("📅 开始生成明日推送计划汇总...")

    try:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        config = cm.load_config()
        channels = {ch.name: ch for ch in config.channels}

        events = []
        for rule in config.messages:
            if not rule.enabled:
                continue

            channel_names = rule.channels or []
            if not channel_names:
                continue

            try:
                trigger_times = get_trigger_times_for_date(rule.original_schedule, tomorrow)
            except Exception as e:
                logger.warning(f"跳过规则 {rule.id}: Cron 解析失败 ({e})")
                continue

            if not trigger_times:
                continue

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

        events.sort(key=lambda x: x["time"])

        message = generate_plan_message(tomorrow, events)

        daily_plan_config = config.daily_plan
        if daily_plan_config is None:
            target_channels = ["bark"]
        else:
            target_channels = daily_plan_config.channels or ["bark"]

        if not target_channels:
            logger.warning("⚠️ 未配置推送计划汇总的发送渠道，跳过发送")
            return

        success_count = 0
        total_count = len(target_channels)

        for ch_name in target_channels:
            if ch_name not in channels:
                logger.warning(f"⚠️ 渠道 '{ch_name}' 不存在，跳过")
                continue

            channel_conf = channels[ch_name]
            data = {
                "title": f"📅 明日推送计划 ({tomorrow.strftime('%Y-%m-%d')})",
                "group": "SparrowPlan"
            }

            try:
                success = await send_push(channel_conf, message, data)
                if success:
                    success_count += 1
                    logger.info(f"✅ 明日推送计划已发送到 '{ch_name}'")
                else:
                    logger.error(f"❌ 发送明日推送计划到 '{ch_name}' 失败")
            except Exception as e:
                logger.error(f"💥 发送明日推送计划到 '{ch_name}' 异常: {e}")

        logger.info(f"📅 明日推送计划汇总完成: {success_count}/{total_count} 个渠道成功")

    except Exception as e:
        logger.error(f"💥 生成明日推送计划失败: {e}", exc_info=True)
