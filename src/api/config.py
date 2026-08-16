"""
配置管理 API（无鉴权版）
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.models import MessageRule, SparrowConfig
from src.core import config_manager as cm
from src.utils.cron_helper import calculate_actual_cron, format_schedule_display

router = APIRouter(prefix="/api/config", tags=["Config"])


# ============ 全量配置 ============
@router.get("/full")
async def get_full_config() -> SparrowConfig:
    """获取完整配置"""
    return cm.load_config()


@router.post("/reload")
async def reload_config() -> dict:
    """热加载配置"""
    try:
        config = cm.reload_config()
        return {"code": 0, "msg": "配置已重新加载", "data": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 消息规则 CRUD ============
@router.get("/rules")
async def list_rules() -> List[dict]:
    """获取所有消息规则（附带计算后的实际时间）"""
    rules = cm.get_all_rules()
    result = []
    for rule in rules:
        item = rule.model_dump()
        actual_cron = calculate_actual_cron(
            rule.original_schedule,
            rule.advance_value,
            rule.advance_unit
        )
        item["actual_schedule"] = actual_cron
        display = format_schedule_display(
            rule.original_schedule,
            actual_cron,
            rule.advance_value,
            rule.advance_unit
        )
        item["display"] = display
        result.append(item)
    return result


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str) -> dict:
    rule = cm.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    item = rule.model_dump()
    actual_cron = calculate_actual_cron(
        rule.original_schedule,
        rule.advance_value,
        rule.advance_unit
    )
    item["actual_schedule"] = actual_cron
    item["display"] = format_schedule_display(
        rule.original_schedule,
        actual_cron,
        rule.advance_value,
        rule.advance_unit
    )
    return item


@router.post("/rules")
async def create_rule(rule: MessageRule) -> dict:
    try:
        cm.add_rule(rule)
        return {"code": 0, "msg": "规则创建成功", "data": rule.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, updates: Dict[str, Any]) -> dict:
    try:
        if "id" in updates:
            del updates["id"]
        updated = cm.update_rule(rule_id, updates)
        return {"code": 0, "msg": "规则更新成功", "data": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str) -> dict:
    success = cm.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="规则不存在")
    return {"code": 0, "msg": "规则已删除"}


# ============ 渠道 CRUD ============
@router.get("/channels")
async def list_channels() -> List[dict]:
    channels = cm.get_all_channels()
    return [ch.model_dump() for ch in channels]


@router.put("/channels/{channel_name}")
async def update_channel(channel_name: str, updates: Dict[str, Any]) -> dict:
    try:
        updated = cm.update_channel(channel_name, updates)
        return {"code": 0, "msg": "渠道更新成功", "data": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))