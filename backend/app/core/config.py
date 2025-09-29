from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "HiLabs Healthcare Contract Classifier"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/contracts.db")
    
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    allowed_origins: list = ["*"]
    allowed_hosts: list = ["localhost", "127.0.0.1", "backend", "*"]
    
    max_file_size: int = 500 * 1024 * 1024
    allowed_file_types: list = ["application/pdf"]
    allowed_states: list = ["TN", "WA"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

def get_settings() -> Settings:
    """Get settings instance"""
    return settings
