"""
Executor configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Executor settings"""
    
    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Kubernetes
    K8S_IN_CLUSTER: bool = True
    KUBECONFIG_PATH: Optional[str] = None
    
    # Database URL for audit logging
    DATABASE_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
