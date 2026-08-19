"""
配置管理 API（无鉴权版）
包含完整的 CRUD 路由：GET、POST、PUT、DELETE
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.models import MessageRule, SparrowConfig
from src.core import config_manager as cm

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
        # 触发调度器重载
        from src.core.scheduler import init_scheduler
        init_scheduler()
        return {"code": 0, "msg": "配置已重新加载，调度器已更新", "data": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 消息规则 CRUD ============

@router.get("/rules")
async def list_rules() -> List[dict]:
    """获取所有消息规则"""
    rules = cm.get_all_rules()
    result = []
    for rule in rules:
        item = rule.model_dump()
        # 直接使用 original_schedule 作为实际执行时间
        item["actual_schedule"] = rule.original_schedule
        item["display"] = {
            "original_display": rule.original_schedule,
            "actual_display": rule.original_schedule,
            "original_raw": rule.original_schedule,
            "actual_raw": rule.original_schedule
        }
        result.append(item)
    return result


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str) -> dict:
    rule = cm.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    item = rule.model_dump()
    item["actual_schedule"] = rule.original_schedule
    item["display"] = {
        "original_display": rule.original_schedule,
        "actual_display": rule.original_schedule,
        "original_raw": rule.original_schedule,
        "actual_raw": rule.original_schedule
    }
    return item


@router.post("/rules")
async def create_rule(rule: MessageRule) -> dict:
    try:
        cm.add_rule(rule)
        # 创建后重载调度器
        from src.core.scheduler import init_scheduler
        init_scheduler()
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
        if "display" in updates:
            del updates["display"]

        updated = cm.update_rule(rule_id, updates)
        # 更新后重载调度器
        from src.core.scheduler import init_scheduler
        init_scheduler()
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
    # 删除后重载调度器
    from src.core.scheduler import init_scheduler
    init_scheduler()
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