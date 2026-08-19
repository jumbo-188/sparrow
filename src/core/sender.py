"""
推送执行引擎 - 渠道适配器
支持：PushPlus、Bark、Bark Group
"""

import os
import json
import httpx
import logging
from jinja2 import Template
from typing import Dict, Any, List

from src.models import ChannelConfig, BarkChildConfig

logger = logging.getLogger(__name__)


async def send_push(channel_conf: ChannelConfig, template_str: str, data: Dict[str, Any]) -> bool:
    """
    统一推送入口
    根据 channel_conf.type 路由到不同的适配器
    """
    try:
        tmpl = Template(template_str)
        rendered_message = tmpl.render(**data)
    except Exception as e:
        logger.error(f"模板渲染失败: {e}")
        return False

    channel_type = channel_conf.type
    if channel_type == "pushplus":
        return await _send_pushplus(channel_conf, rendered_message, data)
    elif channel_type == "bark":
        return await _send_bark(channel_conf, rendered_message, data)
    elif channel_type == "bark_group":
        return await _send_bark_group(channel_conf, rendered_message, data)
    else:
        return await _send_webhook(channel_conf, rendered_message, data)


# ============ Bark 组适配器 ============
async def _send_bark_group(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    """
    Bark 组推送：遍历所有子终端，分别推送
    返回 True 表示所有子终端都推送成功，否则返回 False
    """
    if not channel_conf.children:
        logger.error(f"❌ Bark 组 '{channel_conf.name}' 没有子终端配置")
        return False

    success_count = 0
    total_count = len(channel_conf.children)

    for child in channel_conf.children:
        # 为每个子终端构造一个临时的 ChannelConfig
        child_conf = ChannelConfig(
            name=f"{channel_conf.name}_{child.name}",
            type="bark",
            url=child.url,
            method="POST",
            headers={"Content-Type": "application/json"},
            default_group=child.default_group or channel_conf.default_group or "Sparrow",
            default_icon=child.default_icon or channel_conf.default_icon or ""
        )

        try:
            result = await _send_bark(child_conf, message, data)
            if result:
                success_count += 1
                logger.info(f"✅ Bark 子终端 [{child.name}] 推送成功")
            else:
                logger.error(f"❌ Bark 子终端 [{child.name}] 推送失败")
        except Exception as e:
            logger.error(f"💥 Bark 子终端 [{child.name}] 推送异常: {e}")

    if success_count == total_count:
        logger.info(f"✅ Bark 组 '{channel_conf.name}' 全部推送成功 ({total_count}/{total_count})")
        return True
    else:
        logger.warning(f"⚠️ Bark 组 '{channel_conf.name}' 部分推送成功 ({success_count}/{total_count})")
        return False


# ============ 原有 Bark 适配器（保持不变） ============
async def _send_bark(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    """Bark 推送 (POST)"""
    # 替换 URL 中的环境变量
    import re
    url = channel_conf.url
    # 支持 ${ENV_VAR} 格式
    pattern = re.compile(r'\$\{([^}]+)\}')
    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, f"MISSING_ENV_{var_name}")
    url = pattern.sub(replacer, url)

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

    # 清理空值
    if isinstance(payload["badge"], str) and payload["badge"].isdigit():
        payload["badge"] = int(payload["badge"])
    elif not isinstance(payload["badge"], int):
        payload["badge"] = 1

    payload = {k: v for k, v in payload.items() if v is not None and v != ""}
    if "badge" not in payload:
        payload["badge"] = 1

    logger.debug(f"Bark 请求体: {json.dumps(payload, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 200:
                logger.info(f"✅ Bark 推送成功")
                return True
            else:
                logger.error(f"❌ Bark 返回错误: {result}")
                return False
    except Exception as e:
        logger.error(f"❌ Bark 请求异常: {e}")
        return False


# ============ PushPlus 适配器（保持不变） ============
async def _send_pushplus(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    # ... 保持原有代码不变 ...
    pass


# ============ 通用 Webhook 适配器（保持不变） ============
async def _send_webhook(channel_conf: ChannelConfig, message: str, data: Dict[str, Any]) -> bool:
    # ... 保持原有代码不变 ...
    pass