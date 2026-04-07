"""
API v1 Router
Aggregates all v1 endpoints
"""

from fastapi import APIRouter
from .endpoints import chat, status, actions

router = APIRouter()

# Include sub-routers
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(status.router, prefix="/status", tags=["Status"])
router.include_router(actions.router, prefix="/actions", tags=["Actions"])
