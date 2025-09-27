from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "HiLabs Healthcare Contract Classifier"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    database_url: str = "sqlite:///./contracts.db"
    
    redis_url: str = "redis://localhost:6379"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    allowed_origins: list = ["*"]
    allowed_hosts: list = ["localhost", "127.0.0.1", "backend", "*"]
    
    max_file_size: int = 10 * 1024 * 1024
    allowed_file_types: list = ["application/pdf"]
    allowed_states: list = ["TN", "WA"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get settings instance"""
    return settings
