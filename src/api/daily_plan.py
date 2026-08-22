"""
每日计划汇总配置 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.core import config_manager as cm
from src.models import DailyPlanConfig
from src.core.planner_sender import send_daily_plan

router = APIRouter(prefix="/api/daily-plan", tags=["DailyPlan"])


class DailyPlanUpdate(BaseModel):
    time: str = "20:00"
    channels: List[str] = ["bark"]


@router.get("/config")
async def get_daily_plan_config():
    """获取每日计划汇总配置"""
    config = cm.load_config()
    daily_plan = config.daily_plan

    if daily_plan is None:
        return {
            "code": 0,
            "data": {
                "time": "20:00",
                "channels": ["bark"],
                "enabled": False
            }
        }

    return {
        "code": 0,
        "data": {
            "time": daily_plan.time,
            "channels": daily_plan.channels or ["bark"],
            "enabled": True
        }
    }


@router.put("/config")
async def update_daily_plan_config(update: DailyPlanUpdate):
    """更新每日计划汇总配置"""
    try:
        config = cm.load_config()

        # 创建或更新 daily_plan 配置
        config.daily_plan = DailyPlanConfig(
            time=update.time,
            channels=update.channels
        )

        cm.save_config(config)

        # 重载调度器以应用新时间
        from src.core.scheduler import init_scheduler
        init_scheduler()

        return {
            "code": 0,
            "msg": "配置已更新，调度器已重载",
            "data": {
                "time": update.time,
                "channels": update.channels
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_daily_plan():
    """手动测试发送明日计划汇总"""
    try:
        await send_daily_plan()
        return {"code": 0, "msg": "测试推送已发送，请检查手机通知"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))