"""
Kubernetes action executor API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.k8s.client import get_k8s_client, KubernetesClient
from app.core.audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ExecuteActionRequest(BaseModel):
    action_type: str = Field(..., description="Type of action (delete_pod, restart_deployment, scale_deployment, etc.)")
    namespace: str = Field(..., description="Kubernetes namespace")
    resource_type: str = Field(..., description="Resource type (pod, deployment, etc.)")
    resource_name: str = Field(..., description="Resource name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    dry_run: bool = Field(True, description="Perform dry run")
    requested_by: str = Field(..., description="User requesting the action")


class ActionResult(BaseModel):
    success: bool
    action: str
    resource: str
    namespace: str
    dry_run: bool
    result: Dict[str, Any]
    message: str


@router.post("/execute", response_model=ActionResult, tags=["Actions"])
async def execute_action(
    request: ExecuteActionRequest,
    k8s_client: KubernetesClient = Depends(get_k8s_client)
):
    """Execute a Kubernetes action"""
    logger.info(f"Executing action: {request.action_type} on {request.resource_type}/{request.resource_name}")
    
    try:
        result = None
        
        if request.action_type == "delete_pod":
            result = await k8s_client.delete_pod(
                name=request.resource_name,
                namespace=request.namespace,
                dry_run=request.dry_run
            )
            
        elif request.action_type == "restart_deployment":
            result = await k8s_client.restart_deployment(
                name=request.resource_name,
                namespace=request.namespace,
                dry_run=request.dry_run
            )
            
        elif request.action_type == "scale_deployment":
            replicas = request.parameters.get("replicas")
            if replicas is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'replicas' parameter for scale_deployment action"
                )
            result = await k8s_client.scale_deployment(
                name=request.resource_name,
                namespace=request.namespace,
                replicas=replicas,
                dry_run=request.dry_run
            )
            
        elif request.action_type == "rollback_deployment":
            revision = request.parameters.get("revision") if request.parameters else None
            result = await k8s_client.rollback_deployment(
                name=request.resource_name,
                namespace=request.namespace,
                revision=revision,
                dry_run=request.dry_run
            )
            
        elif request.action_type == "update_configmap":
            data = request.parameters.get("data")
            if data is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'data' parameter for update_configmap action"
                )
            result = await k8s_client.update_configmap(
                name=request.resource_name,
                namespace=request.namespace,
                data=data,
                dry_run=request.dry_run
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action type: {request.action_type}"
            )
        
        # Log action
        await log_action(
            action=request.action_type,
            resource_type=request.resource_type,
            resource_name=request.resource_name,
            namespace=request.namespace,
            user=request.requested_by,
            result="success",
            dry_run=request.dry_run,
            details=result
        )
        
        return ActionResult(
            success=True,
            action=request.action_type,
            resource=f"{request.resource_type}/{request.resource_name}",
            namespace=request.namespace,
            dry_run=request.dry_run,
            result=result,
            message=f"Action {request.action_type} completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Action execution failed: {e}", exc_info=True)
        
        # Log failure
        await log_action(
            action=request.action_type,
            resource_type=request.resource_type,
            resource_name=request.resource_name,
            namespace=request.namespace,
            user=request.requested_by,
            result="failure",
            dry_run=request.dry_run,
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action execution failed: {str(e)}"
        )


@router.get("/resources/{namespace}", tags=["Resources"])
async def list_resources(
    namespace: str,
    resource_type: str = "pod",
    k8s_client: KubernetesClient = Depends(get_k8s_client)
):
    """List resources in a namespace"""
    try:
        if resource_type == "pod":
            resources = await k8s_client.get_pods(namespace=namespace)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported resource type: {resource_type}"
            )
        
        return {
            "namespace": namespace,
            "resource_type": resource_type,
            "count": len(resources),
            "resources": resources
        }
    except Exception as e:
        logger.error(f"Failed to list resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/deployment/{namespace}/{name}/status", tags=["Resources"])
async def get_deployment_status(
    namespace: str,
    name: str,
    k8s_client: KubernetesClient = Depends(get_k8s_client)
):
    """Get deployment status"""
    try:
        status_info = await k8s_client.get_deployment_status(
            name=name,
            namespace=namespace
        )
        return status_info
    except Exception as e:
        logger.error(f"Failed to get deployment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/nodes", tags=["Resources"])
async def list_nodes(k8s_client: KubernetesClient = Depends(get_k8s_client)):
    """List all nodes"""
    try:
        nodes = await k8s_client.get_node_status()
        return {
            "count": len(nodes),
            "nodes": nodes
        }
    except Exception as e:
        logger.error(f"Failed to list nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/namespaces", tags=["Resources"])
async def list_namespaces(k8s_client: KubernetesClient = Depends(get_k8s_client)):
    """List all namespaces"""
    try:
        namespaces = await k8s_client.list_namespaces()
        return {
            "count": len(namespaces),
            "namespaces": namespaces
        }
    except Exception as e:
        logger.error(f"Failed to list namespaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
