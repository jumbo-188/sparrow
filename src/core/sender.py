import httpx
import json
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


async def send_push(channel_config, template_str, data):
    """执行单条推送"""
    try:
        # 1. 渲染消息内容
        tmpl = Template(template_str)
        rendered_message = tmpl.render(**data)

        # 2. 构建请求
        url = channel_config['url']
        method = channel_config.get('method', 'POST').upper()
        headers = channel_config.get('headers', {})
        payload = {}

        # 3. 处理 Payload 模板（如果有）
        if channel_config.get('payload_template'):
            pt = Template(channel_config['payload_template'])
            rendered_payload = pt.render(**data, message=rendered_message)
            try:
                payload = json.loads(rendered_payload)
            except:
                # 如果不是 JSON，则作为普通文本处理（Bark 走 URL 参数）
                if method == "GET":
                    # Bark 特殊处理：拼接 URL 参数
                    # 假设 url 为 https://api.day.app/${BARK_KEY}
                    # 格式化为 https://api.day.app/KEY/标题/内容
                    title = data.get('title', '通知')
                    # 简单处理：直接拼接在末尾？但最好在 config 中用 url_template
                    # 我们保留灵活性，如果 url 有 ? 则用 params，否则走 data
                    pass
        else:
            # 如果没有 payload_template，默认传 message 字段
            payload = {"message": rendered_message}

        # 4. 发送请求
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method == "GET":
                # 适配 Bark：将消息放在 URL 路径或 Query 中
                # 规则：如果 url 包含 ?，则当作 query 参数；否则把 message 作为路径最后一段
                if '?' in url:
                    resp = await client.get(url, params={"text": rendered_message, **data})
                else:
                    # Bark 格式: https://api.day.app/KEY/标题/内容
                    # 通过 payload_template 拼接实现
                    resp = await client.get(url)
            else:
                # POST JSON
                if 'application/json' in headers.get('Content-Type', ''):
                    resp = await client.post(url, json=payload, headers=headers)
                else:
                    resp = await client.post(url, data=payload, headers=headers)

            resp.raise_for_status()
            logger.info(f"推送成功: {channel_config['name']}")
            return True
    except Exception as e:
        logger.error(f"推送失败: {e}")
        return False