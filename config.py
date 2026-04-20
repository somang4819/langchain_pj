# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

# .env 파일 경로
from pathlib import Path
env_path = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    # ==================== 데이터베이스 ====================
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False
    
    # ==================== 환경 ====================
    environment: str = "development"
    debug: bool = True
    
    # ==================== FastAPI ====================
    app_name: str = "LangChain API"
    api_version: str = "1.0.0"
    
    # ==================== API ====================
    api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache
def get_settings():
    return Settings()

# 테스트 (개발용)
if __name__ == "__main__":
    settings = get_settings()
    print(f"DATABASE_URL: {settings.database_url}")
    print(f"ENVIRONMENT: {settings.environment}")
    print(f"DEBUG: {settings.debug}")