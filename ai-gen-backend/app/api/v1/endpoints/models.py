"""
模型管理 API 端点
"""
from typing import Optional, List
from fastapi import APIRouter, Depends

from app.api.v1.schemas.common import Response
from app.services.ai_service import AIClientFactory
from app.core.dependencies import check_rate_limit

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("")
async def list_models(
        provider: Optional[str] = None,
        _: str = Depends(check_rate_limit)
):
    """
    获取可用模型列表

    - **provider**: 可选，过滤提供商 (yi/bailian)
    """
    all_models = []

    providers = [provider] if provider else ["yi", "bailian"]

    for p in providers:
        models = AIClientFactory.get_models_for_provider(p)
        for model in models:
            model["provider"] = p
            all_models.append(model)

    return Response.success({
        "models": all_models,
        "total": len(all_models)
    })


@router.get("/providers")
async def list_providers(
        _: str = Depends(check_rate_limit)
):
    """
    获取所有可用的提供商
    """
    return Response.success({
        "providers": AIClientFactory.get_available_providers()
    })


@router.get("/{provider}")
async def get_models_by_provider(
        provider: str,
        _: str = Depends(check_rate_limit)
):
    """
    获取指定提供商的模型列表

    - **provider**: 提供商名称 (yi/bailian)
    """
    models = AIClientFactory.get_models_for_provider(provider)

    if not models:
        return Response.error(f"提供商 '{provider}' 不存在或没有可用模型", 404)

    return Response.success({
        "provider": provider,
        "models": models,
        "total": len(models)
    })