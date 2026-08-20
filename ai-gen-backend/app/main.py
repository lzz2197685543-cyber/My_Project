"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from pathlib import Path

from config.settings import settings
from app.api.v1.router import router as api_v1_router
from app.core.exceptions import register_exception_handlers
from app.utils.logger import get_logger

logger = get_logger("main")

# ==================== 创建应用 ====================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 生成后端服务 - 支持聊天、文生图、图生图、多图融合",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.DEBUG
)

# ==================== 注册异常处理器 ====================

register_exception_handlers(app)

# ==================== CORS 配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# ==================== 静态文件服务 ====================

# 输出目录挂载
output_dir = settings.OUTPUT_DIR
if output_dir.exists():
    app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")
    logger.info(f"📁 静态文件服务: /output -> {output_dir}")

# ✅ 输入目录挂载 - 用于访问上传的图片
input_dir = settings.INPUT_DIR
if input_dir.exists():
    app.mount("/data/input", StaticFiles(directory=str(input_dir)), name="input")
    logger.info(f"📁 静态文件服务: /data/input -> {input_dir}")

# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }


# ==================== 自定义 OpenAPI 文档 ====================

def custom_openapi():
    """自定义 OpenAPI 文档"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI 生成后端服务 - 支持聊天、文生图、图生图、多图融合",
        routes=app.routes,
    )

    # 添加 API Key 安全配置
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key 认证 (通过 X-API-Key 头传递)"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Bearer Token 认证 (通过 Authorization: Bearer <token> 头传递)"
        }
    }

    # 为所有需要认证的路径添加安全要求
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if path.startswith("/api/v1/"):
                openapi_schema["paths"][path][method]["security"] = [
                    {"APIKeyHeader": []},
                    {"BearerAuth": []}
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ==================== 启动和关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    logger.info(f"📍 配置目录: {settings.BASE_DIR / 'config'}")
    logger.info(f"📁 数据目录: {settings.DATA_DIR}")
    logger.info(f"📁 输入目录: {settings.INPUT_DIR}")
    logger.info(f"📁 输出目录: {settings.OUTPUT_DIR}")
    logger.info(f"📁 日志目录: {settings.LOGS_DIR}")
    logger.info(f"🔧 调试模式: {settings.DEBUG}")
    logger.info(f"🔑 API易 Key: {'已配置' if settings.YI_API_KEY else '未配置'}")
    logger.info(f"🔑 百炼 Key: {'已配置' if settings.BAILIAN_API_KEY else '未配置'}")
    logger.info("=" * 60)

    # 确保必要目录存在
    settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 应用正在关闭...")


# ==================== 开发入口 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )