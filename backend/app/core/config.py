"""
Core configuration management
Loads settings from environment variables and secrets
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    PROJECT_NAME: str = "AI SRE Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    PORT: int = 8000
    
    # API Keys and Secrets
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis (for caching and rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_TTL: int = 3600
    
    # AI Engine
    AI_ENGINE_URL: str = "http://ai-engine:8001"
    AI_ENGINE_TIMEOUT: int = 30
    
    # Observability Collector
    COLLECTOR_URL: str = "http://collector:8002"
    COLLECTOR_TIMEOUT: int = 10
    
    # Action Executor
    EXECUTOR_URL: str = "http://executor:8003"
    EXECUTOR_TIMEOUT: int = 30
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"  # ollama or openai
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"  # or mistral, codellama, etc.
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_NUM_CTX: int = 4096  # Context window size
    OLLAMA_NUM_PREDICT: int = 2000  # Max tokens to generate
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_TOP_K: int = 40
    
    # OpenAI Configuration (optional fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # GCP Configuration
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: Optional[str] = None
    GCS_BUCKET_ARTIFACTS: Optional[str] = None
    
    # Kubernetes
    KUBECONFIG_PATH: Optional[str] = None
    K8S_IN_CLUSTER: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Authentication
    AUTH_ENABLED: bool = True
    AUTH_BYPASS_PATHS: List[str] = [
        "/health",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Feature Flags
    ENABLE_CHAT: bool = True
    ENABLE_AUTO_REMEDIATION: bool = False
    ENABLE_APPROVAL_WORKFLOW: bool = True
    
    # Storage
    VECTOR_DB_PATH: str = "/data/vector_db"
    EMBEDDINGS_MODEL: str = "nomic-embed-text"  # For Ollama
    EMBEDDING_DIMENSION: int = 768  # nomic-embed-text dimension
    
    # Timeouts
    REQUEST_TIMEOUT: int = 300
    GRACEFUL_SHUTDOWN_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
