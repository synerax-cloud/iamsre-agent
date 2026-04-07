"""
AI Engine - RAG-Based Reasoning Service
Handles AI reasoning, root cause analysis, and recommendations
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1 import router as api_v1_router
from app.rag.vector_store import get_vector_store
from app.core.llm_client import get_llm_client

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI Engine...")
    
    # Initialize LLM client
    try:
        llm_client = get_llm_client()
        logger.info(f"LLM client initialized (provider: {settings.LLM_PROVIDER})")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize vector store
    try:
        vector_store = await get_vector_store()
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Vector store initialization failed: {e}")
    
    yield
    
    logger.info("Shutting down AI Engine...")


app = FastAPI(
    title="AI Engine",
    description="AI Reasoning Engine with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-engine",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check"""
    try:
        # Test LLM connectivity
        llm_client = get_llm_client()
        
        return {
            "status": "ready",
            "service": "ai-engine",
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.OPENAI_MODEL,
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI Engine not ready: {str(e)}"
        )


app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "AI Engine",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "health": "/health",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info",
    )
