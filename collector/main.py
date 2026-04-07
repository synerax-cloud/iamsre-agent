"""
Observability Collector - Metrics, Logs, and Events
Collects observability data from Kubernetes and monitoring systems
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1 import router as api_v1_router
from app.collectors.k8s_client import get_k8s_client

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Observability Collector...")
    
    # Initialize K8s client
    try:
        k8s_client = await get_k8s_client()
        logger.info("Kubernetes client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        if settings. ENVIRONMENT == "production":
            raise
    
    yield
    
    logger.info("Shutting down Observability Collector...")


app = FastAPI(
    title="Observability Collector",
    description="Collects metrics, logs, and events from Kubernetes",
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
        "service": "collector",
        "version": "1.0.0",
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check"""
    try:
        k8s_client = await get_k8s_client()
        # Test connection
        namespaces = await k8s_client.list_namespaces()
        
        return {
            "status": "ready",
            "service": "collector",
            "kubernetes": "connected",
            "prometheus": settings.PROMETHEUS_URL if settings.PROMETHEUS_URL else "not configured",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Collector not ready: {str(e)}"
        )


app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Observability Collector",
        "version": "1.0.0",
        "health": "/health",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG,
        log_level="info",
    )
