"""
Kubernetes client for collector
"""

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class K8sCollector:
    """Kubernetes metrics and events collector"""
    
    def __init__(self):
        self.initialized = False
        self._core_v1 = None
        self._apps_v1 = None
        self._metrics_client = None
        
    async def initialize(self):
        """Initialize Kubernetes client"""
        if self.initialized:
            return
            
        try:
            if settings.K8S_IN_CLUSTER:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration")
            else:
                config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
                logger.info("Loaded Kubernetes configuration from kubeconfig")
            
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    async def list_namespaces(self) -> List[str]:
        """List all namespaces"""
        try:
            namespaces = self._core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            logger.error(f"Failed to list namespaces: {e}")
            raise
    
    async def get_pod_metrics(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pod metrics"""
        try:
            if namespace:
                pods = self._core_v1.list_namespaced_pod(namespace=namespace)
            else:
                pods = self._core_v1.list_pod_for_all_namespaces()
            
            metrics = []
            for pod in pods.items:
                pod_metric = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "containers": len(pod.spec.containers),
                    "restart_count": sum(cs.restart_count for cs in pod.status.container_statuses or []),
                    "cpu_request": self._get_resource_requests(pod, "cpu"),
                    "memory_request": self._get_resource_requests(pod, "memory"),
                    "created_at": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                }
                
                # Check for issues
                if pod.status.phase not in ["Running", "Succeeded"]:
                    pod_metric["issue"] = f"Pod in {pod.status.phase} state"
                elif pod_metric["restart_count"] > 5:
                    pod_metric["issue"] = f"High restart count: {pod_metric['restart_count']}"
                
                metrics.append(pod_metric)
            
            return metrics
        except ApiException as e:
            logger.error(f"Failed to get pod metrics: {e}")
            raise
    
    async def get_deployment_metrics(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deployment metrics"""
        try:
            if namespace:
                deployments = self._apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                deployments = self._apps_v1.list_deployment_for_all_namespaces()
            
            metrics = []
            for deployment in deployments.items:
                deploy_metric = {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": {
                        "desired": deployment.spec.replicas,
                        "current": deployment.status.replicas or 0,
                        "ready": deployment.status.ready_replicas or 0,
                        "updated": deployment.status.updated_replicas or 0,
                        "available": deployment.status.available_replicas or 0,
                    },
                    "strategy": deployment.spec.strategy.type,
                    "created_at": deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None,
                }
                
                # Check for issues
                if deploy_metric["replicas"]["ready"] < deploy_metric["replicas"]["desired"]:
                    deploy_metric["issue"] = f"Not all replicas ready: {deploy_metric['replicas']['ready']}/{deploy_metric['replicas']['desired']}"
                
                metrics.append(deploy_metric)
            
            return metrics
        except ApiException as e:
            logger.error(f"Failed to get deployment metrics: {e}")
            raise
    
    async def get_node_metrics(self) -> List[Dict[str, Any]]:
        """Get node metrics"""
        try:
            nodes = self._core_v1.list_node()
            
            metrics = []
            for node in nodes.items:
                node_metric = {
                    "name": node.metadata.name,
                    "status": "Ready" if any(c.type == "Ready" and c.status == "True" for c in node.status.conditions) else "NotReady",
                    "roles": [label.split("/")[1] for label in node.metadata.labels if label.startswith("node-role.kubernetes.io/")],
                    "version": node.status.node_info.kubelet_version,
                    "capacity": {
                        "cpu": node.status.capacity.get("cpu"),
                        "memory": node.status.capacity.get("memory"),
                        "pods": node.status.capacity.get("pods"),
                    },
                    "allocatable": {
                        "cpu": node.status.allocatable.get("cpu"),
                        "memory": node.status.allocatable.get("memory"),
                        "pods": node.status.allocatable.get("pods"),
                    },
                    "conditions": [
                        {
                            "type": cond.type,
                            "status": cond.status,
                            "reason": cond.reason,
                        }
                        for cond in node.status.conditions
                    ],
                }
                
                # Check for issues
                if node_metric["status"] != "Ready":
                    node_metric["issue"] = f"Node not ready"
                
                metrics.append(node_metric)
            
            return metrics
        except ApiException as e:
            logger.error(f"Failed to get node metrics: {e}")
            raise
    
    async def get_events(
        self,
        namespace: Optional[str] = None,
        limit: int = 100,
        since_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get Kubernetes events"""
        try:
            since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
            
            if namespace:
                events = self._core_v1.list_namespaced_event(namespace=namespace)
            else:
                events = self._core_v1.list_event_for_all_namespaces()
            
            # Filter and format events
            filtered_events = []
            for event in events.items:
                if event.last_timestamp and event.last_timestamp > since_time:
                    filtered_events.append({
                        "namespace": event.metadata.namespace,
                        "name": event.metadata.name,
                        "type": event.type,  # Normal, Warning
                        "reason": event.reason,
                        "message": event.message,
                        "involved_object": {
                            "kind": event.involved_object.kind,
                            "name": event.involved_object.name,
                            "namespace": event.involved_object.namespace,
                        },
                        "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                        "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                        "count": event.count,
                    })
            
            # Sort by timestamp (most recent first)
            filtered_events.sort(key=lambda x: x["last_timestamp"] or "", reverse=True)
            
            return filtered_events[:limit]
        except ApiException as e:
            logger.error(f"Failed to get events: {e}")
            raise
    
    async def get_logs(
        self,
        pod_name: str,
        namespace: str,
        container: Optional[str] = None,
        tail_lines: int = 100
    ) -> str:
        """Get pod logs"""
        try:
            logs = self._core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return logs
        except ApiException as e:
            logger.error(f"Failed to get logs for pod {pod_name}: {e}")
            raise
    
    async def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health summary"""
        try:
            # Get all metrics
            nodes = await self.get_node_metrics()
            pods = await self.get_pod_metrics()
            deployments = await self.get_deployment_metrics()
            events = await self.get_events(since_minutes=30)
            
            # Count issues
            node_issues = [n for n in nodes if n["status"] != "Ready"]
            pod_issues = [p for p in pods if "issue" in p]
            deployment_issues = [d for d in deployments if "issue" in d]
            warning_events = [e for e in events if e["type"] == "Warning"]
            
            # Calculate health score (0-100)
            health_score = 100
            health_score -= len(node_issues) * 20  # Nodes are critical
            health_score -= len(deployment_issues) * 5
            health_score -= min(len(pod_issues), 10) * 2
            health_score -= min(len(warning_events), 10)
            health_score = max(0, health_score)
            
            # Determine status
            if health_score >= 90:
                status_text = "healthy"
            elif health_score >= 70:
                status_text = "degraded"
            else:
                status_text = "critical"
            
            return {
                "health_score": health_score,
                "status": status_text,
                "summary": {
                    "nodes": {
                        "total": len(nodes),
                        "ready": len([n for n in nodes if n["status"] == "Ready"]),
                        "issues": len(node_issues),
                    },
                    "pods": {
                        "total": len(pods),
                        "running": len([p for p in pods if p["status"] == "Running"]),
                        "issues": len(pod_issues),
                    },
                    "deployments": {
                        "total": len(deployments),
                        "healthy": len([d for d in deployments if "issue" not in d]),
                        "issues": len(deployment_issues),
                    },
                    "recent_warnings": len(warning_events),
                },
                "issues": {
                    "nodes": [{"name": n["name"], "issue": n.get("issue")} for n in node_issues],
                    "pods": [{"name": p["name"], "namespace": p["namespace"], "issue": p.get("issue")} for p in pod_issues[:10]],
                    "deployments": [{"name": d["name"], "namespace": d["namespace"], "issue": d.get("issue")} for d in deployment_issues],
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            raise
    
    def _get_resource_requests(self, pod, resource_type: str) -> Optional[str]:
        """Get resource requests for a pod"""
        total = 0
        for container in pod.spec.containers:
            if container.resources and container.resources.requests:
                value = container.resources.requests.get(resource_type)
                if value:
                    return value  # Return raw value (e.g., "100m", "256Mi")
        return None


# Global client instance
_k8s_client: Optional[K8sCollector] = None


async def get_k8s_client() -> K8sCollector:
    """Get or create Kubernetes client instance"""
    global _k8s_client
    if _k8s_client is None:
        _k8s_client = K8sCollector()
        await _k8s_client.initialize()
    return _k8s_client
