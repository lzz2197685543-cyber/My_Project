#!/usr/bin/env python
"""
开发服务器启动脚本
"""
import uvicorn
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config.settings import settings

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    print(f"📍 服务地址: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API 文档: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"📘 ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print(f"🔧 调试模式: {settings.DEBUG}")
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )