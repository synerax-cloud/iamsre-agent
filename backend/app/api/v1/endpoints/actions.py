"""
Action Endpoints
Execute Kubernetes actions
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.schemas import ActionRequest, ActionResponse
from app.core.config import settings
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/execute", response_model=ActionResponse)
async def execute_action(
    request: ActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a Kubernetes action
    
    Supported actions:
    - restart_deployment
    - scale_deployment
    - delete_pod
    - rollback_deployment
    - update_configmap
    """
    try:
        # Validate action type
        valid_actions = [
            "restart_deployment",
            "scale_deployment",
            "delete_pod",
            "rollback_deployment",
            "update_configmap",
            "drain_node"
        ]
        
        if request.action_type not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type. Must be one of: {', '.join(valid_actions)}"
            )
        
        # Call executor service
        async with httpx.AsyncClient() as client:
            executor_response = await client.post(
                f"{settings.EXECUTOR_URL}/api/v1/execute",
                json={
                    "action_type": request.action_type,
                    "params": request.params
                },
                timeout=30.0
            )
            executor_response.raise_for_status()
            executor_data = executor_response.json()
        
        # TODO: Store action in database for audit log
        
        return ActionResponse(
            action_id=executor_data.get("action_id", ""),
            status=executor_data.get("status", "completed"),
            message=executor_data.get("message", ""),
            result=executor_data.get("result", {}),
            timestamp=datetime.utcnow()
        )
        
    except httpx.HTTPError as e:
        logger.error(f"Executor request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executor service is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in execute_action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute action"
        )


@router.get("/history")
async def get_action_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get action execution history"""
    # TODO: Implement database query for action history
    return {
        "actions": [],
        "total": 0
    }


@router.get("/{action_id}")
async def get_action_status(
    action_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get status of a specific action"""
    # TODO: Implement database query
    return {
        "action_id": action_id,
        "status": "completed",
        "message": "Action completed successfully"
    }
