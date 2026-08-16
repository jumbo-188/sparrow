"""
推送执行引擎 - 渠道适配器
支持：PushPlus (/batchSend) 和 Bark (POST)
"""

import os
import json
import httpx
import logging
from jinja2 import Template
from typing import Dict, Any

from src.models import ChannelConfig

logger = logging.getLogger(__name__)


async def send_push(channel_conf: ChannelConfig, template_str: str, data: Dict[str, Any]) -> bool:
    """
    统一推送入口
    根据 channel_conf.type 路由到不同的适配器
    """
    # 1. 渲染消息正文
    try:
        tmpl = Template(template_str)
        rendered_message = tmpl.render(**data)
    except Exception as e:
        logger.error(f"模板渲染失败: {e}")
        return False

    # 2. 根据渠道类型分发
    channel_type = channel_conf.type
    if channel_type == "pushplus":
        return await _send_pushplus(channel_conf, rendered_message, data)
    elif channel_type == "bark":
        return await _send_bark(channel_conf, rendered_message, data)
    else:
        # 通用 Webhook（后续扩展）
        return await _send_webhook(channel_conf, rendered_message, data)


# ============ PushPlus 适配器 ============
async def _send_pushplus(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    """
    PushPlus 批量发送 (/batchSend)
    支持覆盖参数：channel, template, topic
    """
    url = "https://www.pushplus.plus/batchSend"

    # 读取 Token（从环境变量）
    token = os.getenv("PUSHPLUS_TOKEN")
    if not token:
        logger.error("❌ PUSHPLUS_TOKEN 未在 .env 中配置")
        return False

    # 组装请求体（优先级：data > 渠道默认）
    payload = {
        "token": token,
        "title": data.get("title", "Sparrow 通知"),
        "content": message,
        "channel": data.get("pushplus_channel") or channel_conf.default_channel or "wechat",
        "template": data.get("pushplus_template") or channel_conf.default_template or "markdown",
        "topic": data.get("pushplus_topic") or channel_conf.default_topic or ""
    }

    # 移除空值字段（避免 PushPlus 报错）
    payload = {k: v for k, v in payload.items() if v is not None and v != ""}

    logger.debug(f"PushPlus 请求体: {json.dumps(payload, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 200:
                logger.info(f"✅ PushPlus 推送成功: {result.get('msg')}")
                return True
            else:
                logger.error(f"❌ PushPlus 返回错误: {result}")
                return False
    except Exception as e:
        logger.error(f"❌ PushPlus 请求异常: {e}")
        return False


# ============ Bark 适配器 ============
async def _send_bark(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    """
    Bark 推送 (POST)
    支持参数：title, body, group, icon, badge, sound, url, level, automaticallyCopy
    """
    # 从环境变量中读取 BARK_KEY 并替换 URL
    bark_key = os.getenv("BARK_KEY")
    if not bark_key:
        logger.error("❌ BARK_KEY 未在 .env 中配置")
        return False

    # 如果 url 中包含 ${BARK_KEY}，替换它
    url = channel_conf.url.replace("${BARK_KEY}", bark_key)

    # 组装请求体（优先级：data > 渠道默认）
    payload = {
        "title": data.get("title", "Sparrow 通知"),
        "body": message,
        "group": data.get("group") or channel_conf.default_group or "Sparrow",
        "icon": data.get("icon") or channel_conf.default_icon or "",
        "badge": data.get("badge", 1),
        "sound": data.get("sound", "minuet.caf"),
        "url": data.get("url", ""),
        "level": data.get("level", "active"),
        "automaticallyCopy": data.get("automaticallyCopy", 0),
    }

    # 移除空值字段（Bark 对空字符串敏感，部分字段必须为整数）
    # badge 必须是整数，如果传入字符串则转换
    if isinstance(payload["badge"], str) and payload["badge"].isdigit():
        payload["badge"] = int(payload["badge"])
    elif not isinstance(payload["badge"], int):
        payload["badge"] = 1

    # 移除空字符串
    payload = {k: v for k, v in payload.items() if v is not None and v != ""}
    # 但 badge, automaticallyCopy 等数字字段保留 0
    if "badge" not in payload:
        payload["badge"] = 1

    logger.debug(f"Bark 请求体: {json.dumps(payload, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            result = resp.json()
            # Bark 返回格式：{"code":200, "message":"success"}
            if result.get("code") == 200:
                logger.info(f"✅ Bark 推送成功")
                return True
            else:
                logger.error(f"❌ Bark 返回错误: {result}")
                return False
    except Exception as e:
        logger.error(f"❌ Bark 请求异常: {e}")
        return False


# ============ 通用 Webhook 适配器（预留扩展） ============
async def _send_webhook(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    """
    通用 Webhook 适配器（后续扩展钉钉、飞书等）
    """
    logger.warning(f"通用 Webhook 适配器尚未实现，渠道: {channel_conf.name}")
    return False