from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import logging
import os

# 导入路由
from src.api import config as config_api
from src.core.scheduler import init_scheduler

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sparrow Push Service", version="2.0.0")

# ---------- 注册 API 路由 ----------
app.include_router(config_api.router)

# ---------- 静态文件托管（前端界面） ----------
# 预留：未来将 Vue 构建产物放在 frontend/dist 中
frontend_path = "frontend/dist"
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")


    @app.get("/")
    async def serve_frontend():
        return FileResponse(f"{frontend_path}/index.html")
else:
    @app.get("/")
    async def root():
        return {"msg": "Sparrow API Server is running. Frontend not built yet."}


# ---------- 健康检查 ----------
@app.get("/health")
async def health():
    return {"status": "alive", "service": "Sparrow"}


# ---------- 启动调度器 ----------
@app.on_event("startup")
async def startup_event():
    logger.info("🕊️ Sparrow 正在启动...")
    try:
        # 先加载配置校验
        from src.core.config_manager import load_config
        config = load_config()
        logger.info(f"✅ 配置加载成功：{len(config.messages)} 条规则，{len(config.channels)} 个渠道")

        # 启动调度器（Phase 2 会重构这里的逻辑，目前先调用）
        init_scheduler()
        logger.info("✅ 调度器已启动")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    from src.core.scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")

# ---------- 手动测试推送（保留） ----------
# TODO: Phase 2 时会重构到单独的 api/push.py