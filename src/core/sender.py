import httpx
import json
import logging
from jinja2 import Template, Environment, StrictUndefined

logger = logging.getLogger(__name__)


async def send_push(channel_config, template_str, data):
    """
    推送执行器：统一使用 POST + JSON 请求体
    所有消息字段（包括 Bark 的 group/icon）都在 payload_template 中定义
    """
    try:
        # 1. 渲染消息主体（用户看到的文字内容）
        msg_tmpl = Template(template_str)
        rendered_message = msg_tmpl.render(**data)

        # 2. 获取渠道配置
        url = channel_config['url']
        method = channel_config.get('method', 'POST').upper()  # 强制 POST
        headers = channel_config.get('headers', {})

        # 3. 构建最终请求体（核心：支持 group, icon 等所有 Bark 专属字段）
        payload = {}
        if channel_config.get('payload_template'):
            # 使用 Jinja2 渲染 payload（允许未定义变量时使用默认值）
            env = Environment(undefined=StrictUndefined)
            pt = env.from_string(channel_config['payload_template'])

            # 渲染时传入完整数据，并附加上渲染好的消息主体
            # 这样你在模板里既可以用 {{ message }} 也可以用 {{ group }}
            rendered_payload_str = pt.render(**data, message=rendered_message)

            # 尝试解析为 JSON
            try:
                payload = json.loads(rendered_payload_str)
            except json.JSONDecodeError as e:
                logger.error(f"Payload 不是合法 JSON: {rendered_payload_str}, 错误: {e}")
                # 降级处理：如果解析失败，就把渲染结果作为纯文本放在 body 字段
                payload = {"body": rendered_payload_str}
        else:
            # 如果没有配置模板，默认发包
            payload = {"message": rendered_message}

        # 4. 发送 HTTP POST 请求
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 强制 POST（忽略配置里的 GET，因为你要统一用 POST）
            if method.upper() != "POST":
                logger.warning(f"配置为 {method}，但已强制转为 POST 请求")

            # 设置默认 Content-Type 为 JSON
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'

            # 请求体直接传 JSON
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info(f"✅ 推送成功 -> {channel_config['name']} | 状态码: {response.status_code}")
            logger.debug(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
            return True

    except Exception as e:
        logger.error(f"❌ 推送失败: {e}")
        return False