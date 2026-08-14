from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import os

from src.core.scheduler import init_scheduler
from src.utils.config_loader import load_config

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/sparrow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sparrow Push Service (NAS Edition)", version="2.0.0")


# ---------- 服务启动时加载调度器 ----------
@app.on_event("startup")
async def startup_event():
    logger.info("🕊️ Sparrow 正在启动，初始化定时调度器...")
    try:
        init_scheduler()
        logger.info("✅ 所有定时任务已加载，服务就绪！")
    except Exception as e:
        logger.error(f"❌ 调度器启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    from src.core.scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已安全关闭")


# ---------- API 接口 ----------
class PushTestRequest(BaseModel):
    route_id: str
    data: dict = {}


@app.get("/health")
async def health():
    return {"status": "alive", "scheduler": "running", "service": "Sparrow"}


@app.post("/api/v1/reload")
async def reload_config():
    """无需重启容器，重新加载配置"""
    from src.core.scheduler import init_scheduler
    try:
        init_scheduler()
        return {"code": 0, "msg": "配置已重新加载"}
    except Exception as e:
        return {"code": 500, "msg": str(e)}


@app.post("/api/v1/test")
async def test_push(req: PushTestRequest):
    """手动测试推送（不依赖定时）"""
    config = load_config()
    channels = {ch['name']: ch for ch in config.get('channels', [])}
    msg = next((m for m in config.get('messages', []) if m['id'] == req.route_id), None)
    if not msg:
        raise HTTPException(status_code=404, detail="消息规则未找到")

    from src.core.sender import send_push
    import datetime
    data = {"now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **req.data}
    result = await send_push(channels[msg['channel']], msg['template'], data)
    return {"code": 0 if result else 500, "msg": "success" if result else "failed"}