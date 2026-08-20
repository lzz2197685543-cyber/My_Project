"""
API v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.endpoints import chat, image, models

router = APIRouter()# prefix="/v1"

# 注册各模块路由
router.include_router(chat.router)
router.include_router(image.router)
router.include_router(models.router)