"""
Collector API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
import logging

from app.collectors.k8s_client import get_k8s_client
from app.collectors.prometheus_client import get_prometheus_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics/pods", tags=["Metrics"])
async def get_pod_metrics(namespace: Optional[str] = None):
    """Get pod metrics"""
    try:
        k8s_client = await get_k8s_client()
        metrics = await k8s_client.get_pod_metrics(namespace=namespace)
        return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get pod metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics/deployments", tags=["Metrics"])
async def get_deployment_metrics(namespace: Optional[str] = None):
    """Get deployment metrics"""
    try:
        k8s_client = await get_k8s_client()
        metrics = await k8s_client.get_deployment_metrics(namespace=namespace)
        return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get deployment metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics/nodes", tags=["Metrics"])
async def get_node_metrics():
    """Get node metrics"""
    try:
        k8s_client = await get_k8s_client()
        metrics = await k8s_client.get_node_metrics()
        return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get node metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/events", tags=["Events"])
async def get_events(
    namespace: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    since_minutes: int = Query(60, ge=1, le=1440)
):
    """Get Kubernetes events"""
    try:
        k8s_client = await get_k8s_client()
        events = await k8s_client.get_events(
            namespace=namespace,
            limit=limit,
            since_minutes=since_minutes
        )
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/logs/{namespace}/{pod_name}", tags=["Logs"])
async def get_logs(
    namespace: str,
    pod_name: str,
    container: Optional[str] = None,
    tail_lines: int = Query(100, ge=1, le=1000)
):
    """Get pod logs"""
    try:
        k8s_client = await get_k8s_client()
        logs = await k8s_client.get_logs(
            pod_name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
        return {"logs": logs, "pod": pod_name, "namespace": namespace}
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cluster/health", tags=["Cluster"])
async def get_cluster_health():
    """Get overall cluster health"""
    try:
        k8s_client = await get_k8s_client()
        health = await k8s_client.get_cluster_health()
        return health
    except Exception as e:
        logger.error(f"Failed to get cluster health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/prometheus/query", tags=["Prometheus"])
async def prometheus_query(q: str = Query(..., description="PromQL query")):
    """Execute a Prometheus query"""
    prom_client = get_prometheus_client()
    if not prom_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus not configured"
        )
    
    try:
        result = await prom_client.query(q)
        return result
    except Exception as e:
        logger.error(f"Prometheus query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/prometheus/pod-cpu", tags=["Prometheus"])
async def get_pod_cpu_usage(namespace: Optional[str] = None):
    """Get pod CPU usage from Prometheus"""
    prom_client = get_prometheus_client()
    if not prom_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus not configured"
        )
    
    try:
        metrics = await prom_client.get_pod_cpu_usage(namespace=namespace)
        return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get CPU usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/prometheus/pod-memory", tags=["Prometheus"])
async def get_pod_memory_usage(namespace: Optional[str] = None):
    """Get pod memory usage from Prometheus"""
    prom_client = get_prometheus_client()
    if not prom_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus not configured"
        )
    
    try:
        metrics = await prom_client.get_pod_memory_usage(namespace=namespace)
        return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get memory usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
