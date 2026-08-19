from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEEPSEEK_API_KEY:  Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    class Config:
        """Pydantic 配置"""
        env_file = str(Path(__file__).resolve().parent.parent/'config' / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
