"""
Status Endpoints
Get cluster and workload status
"""

from fastapi import APIRouter, HTTPException, Query, status
from app.core.config import settings
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cluster")
async def get_cluster_status():
    """
    Get overall cluster health and metrics
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COLLECTOR_URL}/api/v1/cluster/health",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Collector request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector service is unavailable"
        )


@router.get("/pods")
async def get_pod_status(
    namespace: Optional[str] = Query(None, description="Filter by namespace")
):
    """
    Get pod status across the cluster or in a specific namespace
    """
    try:
        params = {}
        if namespace:
            params["namespace"] = namespace
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COLLECTOR_URL}/api/v1/pods",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Collector request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector service is unavailable"
        )


@router.get("/deployments")
async def get_deployment_status(
    namespace: Optional[str] = Query(None, description="Filter by namespace")
):
    """
    Get deployment status
    """
    try:
        params = {}
        if namespace:
            params["namespace"] = namespace
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COLLECTOR_URL}/api/v1/deployments",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Collector request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector service is unavailable"
        )


@router.get("/nodes")
async def get_node_status():
    """
    Get node health and resource usage
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COLLECTOR_URL}/api/v1/nodes",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Collector request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector service is unavailable"
        )


@router.get("/events")
async def get_cluster_events(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return")
):
    """
    Get recent cluster events
    """
    try:
        params = {"limit": limit}
        if namespace:
            params["namespace"] = namespace
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COLLECTOR_URL}/api/v1/events",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Collector request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector service is unavailable"
        )
