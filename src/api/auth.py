"""
鉴权模块：基于 .env 中的 ADMIN_PASSWORD
"""

import os
from fastapi import HTTPException, Depends, Header
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def verify_password(x_api_key: str = Header(...)) -> bool:
    """
    从请求头中获取 X-API-Key 进行验证
    前端登录后可将密码保存在 localStorage 中，每次请求携带
    """
    if x_api_key != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True


# 依赖注入（用于需要鉴权的路由）
AuthDep = Depends(verify_password)