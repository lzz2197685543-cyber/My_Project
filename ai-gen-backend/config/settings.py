"""
配置管理模块
从 .env 文件加载配置
"""
import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # ========== 应用配置 ==========
    APP_NAME: str = "AI Generation Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ========== 服务器配置 ==========
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ========== API易配置 ==========
    YI_API_KEY: Optional[str] = None
    YI_ACCESS_TOKEN: Optional[str] =None
    YI_BASE_URL: str = "https://api.apiyi.com/v1"

    # ========== 百炼配置 ==========
    BAILIAN_API_KEY: Optional[str] = None
    BAILIAN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ========== 并发限制 ==========
    MAX_CONCURRENT: int = 5
    IMAGE_TIMEOUT: int = 360

    # ========== 路径配置 ==========
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    INPUT_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "input"
    OUTPUT_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "output"
    LOGS_DIR: Path = Path(__file__).resolve().parent.parent / "logs"

    class Config:
        """Pydantic 配置"""
        env_file = str(Path(__file__).resolve().parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保必要目录存在
settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
