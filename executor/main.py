"""
Kubernetes Action Executor - Main Service
Handles Kubernetes actions with approval workflow and audit logging
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1 import router as api_v1_router
from app.k8s.client import get_k8s_client

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Kubernetes Action Executor...")
    
    # Initialize K8s client
    try:
        k8s_client = await get_k8s_client()
        logger.info(f"Kubernetes client initialized (in-cluster: {settings.K8S_IN_CLUSTER})")
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    yield
    
    logger.info("Shutting down Kubernetes Action Executor...")


# Create FastAPI application
app = FastAPI(
    title="Kubernetes Action Executor",
    description="Executes Kubernetes actions with approval workflow",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
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
        "service": "executor",
        "version": "1.0.0",
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check with K8s connectivity"""
    try:
        k8s_client = await get_k8s_client()
        # Test connection by listing namespaces
        namespaces = await k8s_client.list_namespaces()
        return {
            "status": "ready",
            "service": "executor",
            "kubernetes": "connected",
            "namespaces_count": len(namespaces),
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Kubernetes not accessible: {str(e)}"
        )


# Include API router
app.include_router(
    api_v1_router,
    prefix="/api/v1",
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Kubernetes Action Executor",
        "version": "1.0.0",
        "health": "/health",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.DEBUG,
        log_level="info",
    )
