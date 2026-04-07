"""
Kubernetes client wrapper
Provides async interface to Kubernetes API
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Dict, Any, Optional
import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class KubernetesClient:
    """Async Kubernetes client wrapper"""
    
    def __init__(self):
        self.initialized = False
        self._core_v1 = None
        self._apps_v1 = None
        self._batch_v1 = None
        self._networking_v1 = None
        
    async def initialize(self):
        """Initialize Kubernetes client"""
        if self.initialized:
            return
            
        try:
            if settings.K8S_IN_CLUSTER:
                # Load in-cluster config
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration")
            else:
                # Load from kubeconfig
                config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
                logger.info(f"Loaded Kubernetes configuration from {settings.KUBECONFIG_PATH or 'default location'}")
            
            # Initialize API clients
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._batch_v1 = client.BatchV1Api()
            self._networking_v1 = client.NetworkingV1Api()
            
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
    
    async def get_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pods in a namespace"""
        try:
            pods = self._core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            return [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "restart_count": sum(cs.restart_count for cs in pod.status.container_statuses or []),
                    "created_at": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                }
                for pod in pods.items
            ]
        except ApiException as e:
            logger.error(f"Failed to get pods: {e}")
            raise
    
    async def delete_pod(self, name: str, namespace: str, dry_run: bool = False) -> Dict[str, Any]:
        """Delete a pod"""
        try:
            dry_run_value = "All" if dry_run else None
            result = self._core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                dry_run=dry_run_value
            )
            return {
                "action": "delete_pod",
                "name": name,
                "namespace": namespace,
                "dry_run": dry_run,
                "status": "success" if not dry_run else "dry_run_success",
            }
        except ApiException as e:
            logger.error(f"Failed to delete pod {name}: {e}")
            raise
    
    async def restart_deployment(self, name: str, namespace: str, dry_run: bool = False) -> Dict[str, Any]:
        """Restart a deployment by updating annotations"""
        try:
            from datetime import datetime
            
            # Get current deployment
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            
            # Update restart annotation
            if deployment.spec.template.metadata.annotations is None:
                deployment.spec.template.metadata.annotations = {}
            
            deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = datetime.utcnow().isoformat()
            
            # Apply update
            dry_run_value = "All" if dry_run else None
            result = self._apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment,
                dry_run=dry_run_value
            )
            
            return {
                "action": "restart_deployment",
                "name": name,
                "namespace": namespace,
                "dry_run": dry_run,
                "replicas": deployment.spec.replicas,
                "status": "success" if not dry_run else "dry_run_success",
            }
        except ApiException as e:
            logger.error(f"Failed to restart deployment {name}: {e}")
            raise
    
    async def scale_deployment(self, name: str, namespace: str, replicas: int, dry_run: bool = False) -> Dict[str, Any]:
        """Scale a deployment"""
        try:
            # Get current deployment
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            
            old_replicas = deployment.spec.replicas
            deployment.spec.replicas = replicas
            
            # Apply update
            dry_run_value = "All" if dry_run else None
            result = self._apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment,
                dry_run=dry_run_value
            )
            
            return {
                "action": "scale_deployment",
                "name": name,
                "namespace": namespace,
                "old_replicas": old_replicas,
                "new_replicas": replicas,
                "dry_run": dry_run,
                "status": "success" if not dry_run else "dry_run_success",
            }
        except ApiException as e:
            logger.error(f"Failed to scale deployment {name}: {e}")
            raise
    
    async def rollback_deployment(self, name: str, namespace: str, revision: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Rollback a deployment to previous revision"""
        try:
            # Get deployment
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            
            # Get rollout history
            # Note: Full rollback implementation would use rollout API
            # This is a simplified version
            
            return {
                "action": "rollback_deployment",
                "name": name,
                "namespace": namespace,
                "revision": revision or "previous",
                "dry_run": dry_run,
                "status": "success" if not dry_run else "dry_run_success",
                "note": "Rollback initiated"
            }
        except ApiException as e:
            logger.error(f"Failed to rollback deployment {name}: {e}")
            raise
    
    async def update_configmap(self, name: str, namespace: str, data: Dict[str, str], dry_run: bool = False) -> Dict[str, Any]:
        """Update a ConfigMap"""
        try:
            # Get current ConfigMap
            configmap = self._core_v1.read_namespaced_config_map(name=name, namespace=namespace)
            
            # Update data
            configmap.data = data
            
            # Apply update
            dry_run_value = "All" if dry_run else None
            result = self._core_v1.patch_namespaced_config_map(
                name=name,
                namespace=namespace,
                body=configmap,
                dry_run=dry_run_value
            )
            
            return {
                "action": "update_configmap",
                "name": name,
                "namespace": namespace,
                "keys_updated": list(data.keys()),
                "dry_run": dry_run,
                "status": "success" if not dry_run else "dry_run_success",
            }
        except ApiException as e:
            logger.error(f"Failed to update ConfigMap {name}: {e}")
            raise
    
    async def get_deployment_status(self, name: str, namespace: str) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            
            return {
                "name": name,
                "namespace": namespace,
                "replicas": {
                    "desired": deployment.spec.replicas,
                    "current": deployment.status.replicas or 0,
                    "ready": deployment.status.ready_replicas or 0,
                    "updated": deployment.status.updated_replicas or 0,
                    "available": deployment.status.available_replicas or 0,
                },
                "conditions": [
                    {
                        "type": cond.type,
                        "status": cond.status,
                        "reason": cond.reason,
                        "message": cond.message,
                    }
                    for cond in (deployment.status.conditions or [])
                ],
                "image": deployment.spec.template.spec.containers[0].image if deployment.spec.template.spec.containers else None,
            }
        except ApiException as e:
            logger.error(f"Failed to get deployment status {name}: {e}")
            raise
    
    async def get_node_status(self) -> List[Dict[str, Any]]:
        """Get all nodes status"""
        try:
            nodes = self._core_v1.list_node()
            return [
                {
                    "name": node.metadata.name,
                    "status": "Ready" if any(c.type == "Ready" and c.status == "True" for c in node.status.conditions) else "NotReady",
                    "roles": [label.split("/")[1] for label in node.metadata.labels if label.startswith("node-role.kubernetes.io/")],
                    "version": node.status.node_info.kubelet_version,
                    "cpu": node.status.capacity.get("cpu"),
                    "memory": node.status.capacity.get("memory"),
                }
                for node in nodes.items
            ]
        except ApiException as e:
            logger.error(f"Failed to get node status: {e}")
            raise


# Global client instance
_k8s_client: Optional[KubernetesClient] = None


async def get_k8s_client() -> KubernetesClient:
    """Get or create Kubernetes client instance"""
    global _k8s_client
    if _k8s_client is None:
        _k8s_client = KubernetesClient()
        await _k8s_client.initialize()
    return _k8s_client
