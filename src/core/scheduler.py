"""
Sparrow 定时调度器
直接使用 original_schedule 作为执行时间
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.core.sender import send_push
from src.core.config_manager import load_config as load_config_typed

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')


def init_scheduler():
    """初始化调度器，加载所有消息规则"""
    config = load_config_typed()
    channels = {ch.name: ch for ch in config.channels}
    messages = config.messages

    scheduler.remove_all_jobs()

    if not messages:
        logger.warning("⚠️ 未发现任何消息规则")
        return

    for msg in messages:
        if not msg.enabled:
            logger.info(f"⏭️ 消息 {msg.id} 已禁用，跳过")
            continue

        # 直接使用原始 Cron，无需计算提前量
        cron_expr = msg.original_schedule
        logger.debug(f"📅 {msg.id}: 执行时间 {cron_expr}")

        for ch_name in msg.channels:
            if ch_name not in channels:
                logger.error(f"❌ 渠道 '{ch_name}' 未定义，跳过任务 {msg.id}")
                continue

            channel_conf = channels[ch_name]
            job_id = f"{msg.id}_{ch_name}"

            scheduler.add_job(
                func=send_job_wrapper,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[channel_conf, msg.template, msg.data],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=60
            )
            logger.info(f"✅ 已注册定时任务: {msg.id} -> {ch_name} | Cron: {cron_expr}")

    if not scheduler.running:
        scheduler.start()
        logger.info("🚀 APScheduler 调度器已启动")


async def send_job_wrapper(channel_conf, template, default_data):
    """任务执行包装器，注入时间数据"""
    import datetime
    data = {
        "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        **default_data
    }
    try:
        success = await send_push(channel_conf, template, data)
        if success:
            logger.info(f"📨 定时推送成功: {channel_conf.name}")
        else:
            logger.error(f"❌ 定时推送失败: {channel_conf.name}")
    except Exception as e:
        logger.error(f"💥 定时推送异常: {e}", exc_info=True)