"""
配置管理 API
提供 CRUD 接口供前端调用
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.models import MessageRule, SparrowConfig
from src.core import config_manager as cm
from src.utils.cron_helper import calculate_actual_cron, format_schedule_display
from src.api.auth import AuthDep

router = APIRouter(prefix="/api/config", tags=["Config"])


# ============ 全量配置 ============
@router.get("/full")
async def get_full_config(auth: AuthDep) -> SparrowConfig:
    """获取完整配置"""
    return cm.load_config()


@router.post("/reload")
async def reload_config(auth: AuthDep) -> dict:
    """热加载配置（触发调度器更新）"""
    try:
        config = cm.reload_config()
        # TODO: 在 Phase 2 中调用 scheduler.reload_scheduler()
        return {"code": 0, "msg": "配置已重新加载", "data": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 消息规则 CRUD ============
@router.get("/rules")
async def list_rules(auth: AuthDep) -> List[dict]:
    """获取所有消息规则（附带计算后的实际时间）"""
    rules = cm.get_all_rules()
    result = []
    for rule in rules:
        item = rule.model_dump()
        # 计算实际 Cron
        actual_cron = calculate_actual_cron(
            rule.original_schedule,
            rule.advance_value,
            rule.advance_unit
        )
        item["actual_schedule"] = actual_cron

        # 生成展示文本
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
async def get_rule(rule_id: str, auth: AuthDep) -> dict:
    """获取单条规则（含计算时间）"""
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
async def create_rule(rule: MessageRule, auth: AuthDep) -> dict:
    """创建新规则"""
    try:
        cm.add_rule(rule)
        return {"code": 0, "msg": "规则创建成功", "data": rule.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, updates: Dict[str, Any], auth: AuthDep) -> dict:
    """更新规则（部分更新）"""
    try:
        # 过滤掉不可更新的字段（如 id 本身）
        if "id" in updates:
            del updates["id"]
        updated = cm.update_rule(rule_id, updates)
        return {"code": 0, "msg": "规则更新成功", "data": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, auth: AuthDep) -> dict:
    """删除规则"""
    success = cm.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="规则不存在")
    return {"code": 0, "msg": "规则已删除"}


# ============ 渠道 CRUD ============
@router.get("/channels")
async def list_channels(auth: AuthDep) -> List[dict]:
    """获取所有渠道配置"""
    channels = cm.get_all_channels()
    return [ch.model_dump() for ch in channels]


@router.put("/channels/{channel_name}")
async def update_channel(channel_name: str, updates: Dict[str, Any], auth: AuthDep) -> dict:
    """更新渠道配置"""
    try:
        updated = cm.update_channel(channel_name, updates)
        return {"code": 0, "msg": "渠道更新成功", "data": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))