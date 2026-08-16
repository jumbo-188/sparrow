"""
手动推送测试 API（无鉴权版）
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from src.core import config_manager as cm
from src.core.sender import send_push

router = APIRouter(prefix="/api/push", tags=["Push"])

class PushTestRequest(BaseModel):
    rule_id: str
    data: Dict[str, Any] = {}


@router.post("/test")
async def test_push(req: PushTestRequest):
    """手动触发一条消息（不依赖定时）"""
    rule = cm.get_rule(req.rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"规则 '{req.rule_id}' 不存在")

    config = cm.load_config()
    channels = {ch.name: ch for ch in config.channels}

    import datetime
    data = {
        "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        **rule.data,
        **req.data
    }

    results = {}
    for ch_name in rule.channels:
        if ch_name not in channels:
            results[ch_name] = {"success": False, "error": "渠道未定义"}
            continue
        channel_conf = channels[ch_name]
        success = await send_push(channel_conf, rule.template, data)
        results[ch_name] = {"success": success}

    return {
        "code": 0,
        "msg": "测试完成",
        "rule_id": req.rule_id,
        "results": results
    }