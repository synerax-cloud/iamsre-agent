"""
Prometheus client for metrics collection
"""

import httpx
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Prometheus metrics client"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        
    async def query(self, query: str) -> Dict[str, Any]:
        """Execute a PromQL query"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/query",
                    params={"query": query}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Prometheus query failed: {e}")
                raise
    
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Dict[str, Any]:
        """Execute a PromQL range query"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "step": step
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Prometheus range query failed: {e}")
                raise
    
    async def get_pod_cpu_usage(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pod CPU usage"""
        query = 'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace, pod)'
        if namespace:
            query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}",container!=""}}[5m])) by (namespace, pod)'
        
        result = await self.query(query)
        return self._parse_metrics(result)
    
    async def get_pod_memory_usage(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pod memory usage"""
        query = 'sum(container_memory_working_set_bytes{container!=""}) by (namespace, pod)'
        if namespace:
            query = f'sum(container_memory_working_set_bytes{{namespace="{namespace}",container!=""}}) by (namespace, pod)'
        
        result = await self.query(query)
        return self._parse_metrics(result)
    
    async def get_node_cpu_usage(self) -> List[Dict[str, Any]]:
        """Get node CPU usage"""
        query = '100 - (avg by (node) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        result = await self.query(query)
        return self._parse_metrics(result)
    
    async def get_node_memory_usage(self) -> List[Dict[str, Any]]:
        """Get node memory usage"""
        query = '100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes)))'
        result = await self.query(query)
        return self._parse_metrics(result)
    
    def _parse_metrics(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Prometheus query result"""
        metrics = []
        if result.get("status") == "success" and result.get("data", {}).get("result"):
            for item in result["data"]["result"]:
                metric = {
                    "labels": item.get("metric", {}),
                    "value": float(item.get("value", [0, 0])[1]) if item.get("value") else 0
                }
                metrics.append(metric)
        return metrics


def get_prometheus_client() -> Optional[PrometheusClient]:
    """Get Prometheus client if configured"""
    if settings.PROMETHEUS_URL:
        return PrometheusClient(settings.PROMETHEUS_URL)
    return None
