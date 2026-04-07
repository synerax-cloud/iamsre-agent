"""
API v1 router
"""

from fastapi import APIRouter
from app.api.v1 import actions

router = APIRouter()

# Include sub-routers
router.include_router(actions.router, tags=["Actions"])
