"""
配置管理 API（无鉴权版）
包含完整的 CRUD 路由：GET、POST、PUT、DELETE
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.models import MessageRule, SparrowConfig, ChannelConfig
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
    from src.core.scheduler import init_scheduler
    init_scheduler()
    return {"code": 0, "msg": "规则已删除"}


# ============ 渠道 CRUD ============

@router.get("/channels")
async def list_channels() -> List[dict]:
    """获取所有渠道配置"""
    channels = cm.get_all_channels()
    return [ch.model_dump() for ch in channels]


@router.post("/channels")
async def create_channel(channel: ChannelConfig) -> dict:
    """新增渠道"""
    try:
        config = cm.load_config()
        if any(ch.name == channel.name for ch in config.channels):
            raise HTTPException(status_code=400, detail=f"渠道 '{channel.name}' 已存在")

        config.channels.append(channel)
        cm.save_config(config)
        return {"code": 0, "msg": "渠道创建成功", "data": channel.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/channels/{channel_name}")
async def update_channel(channel_name: str, updates: Dict[str, Any]) -> dict:
    """更新渠道配置"""
    try:
        updated = cm.update_channel(channel_name, updates)
        return {"code": 0, "msg": "渠道更新成功", "data": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/channels/{channel_name}")
async def delete_channel(channel_name: str) -> dict:
    """
    删除渠道（简化方案：仅删除渠道，不自动清理规则中的引用）
    删除后请手动编辑相关规则，移除对该渠道的引用
    """
    try:
        config = cm.load_config()
        original_len = len(config.channels)
        config.channels = [ch for ch in config.channels if ch.name != channel_name]
        if len(config.channels) == original_len:
            raise HTTPException(status_code=404, detail="渠道不存在")
        cm.save_config(config)

        # 重载调度器（使变更生效）
        from src.core.scheduler import init_scheduler
        init_scheduler()

        return {
            "code": 0,
            "msg": f"渠道 '{channel_name}' 已删除",
            "warning": "请手动检查消息规则，移除对该渠道的引用，否则推送会失败"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))