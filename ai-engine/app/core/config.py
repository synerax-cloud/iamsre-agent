"""
AI Engine configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """AI Engine settings"""
    
    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # LLM Provider
    LLM_PROVIDER: str = "ollama"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_NUM_CTX: int = 4096
    OLLAMA_NUM_PREDICT: int = 2000
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_TOP_K: int = 40
    
    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Vector Store
    VECTOR_DB_PATH: str = "/data/vector_db"
    EMBEDDING_DIMENSION: int = 768
    
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
