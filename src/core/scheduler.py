from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
from src.core.sender import send_push
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')


def init_scheduler():
    """初始化调度器，加载所有消息规则"""
    config = load_config()
    channels = {ch['name']: ch for ch in config.get('channels', [])}
    messages = config.get('messages', [])

    # 清除已有任务（避免热加载重复）
    scheduler.remove_all_jobs()

    for msg in messages:
        msg_id = msg['id']
        schedule_cron = msg['schedule']
        channel_name = msg['channel']
        template = msg['template']

        if channel_name not in channels:
            logger.error(f"渠道 {channel_name} 未定义，跳过任务 {msg_id}")
            continue

        channel_conf = channels[channel_name]

        # 添加作业
        scheduler.add_job(
            func=send_job_wrapper,
            trigger=CronTrigger.from_crontab(schedule_cron),
            args=[channel_conf, template, msg.get('default_data', {})],
            id=msg_id,
            replace_existing=True,
            misfire_grace_time=60  # 错过执行时间60秒内补发
        )
        logger.info(f"✅ 已注册定时任务: {msg_id} | Cron: {schedule_cron} -> {channel_name}")

    # 启动调度器（如果未启动）
    if not scheduler.running:
        scheduler.start()


async def send_job_wrapper(channel_conf, template, default_data):
    """任务执行包装器，可在此处注入动态数据（如获取实时天气）"""
    import datetime
    # 补充默认数据：当前时间
    data = {
        "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        **default_data  # 配置文件里可写死默认数据
    }
    # 执行推送
    await send_push(channel_conf, template, data)