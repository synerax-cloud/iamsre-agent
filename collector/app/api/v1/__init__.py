"""
API v1 router for collector
"""

from fastapi import APIRouter
from app.api.v1 import collect

router = APIRouter()

router.include_router(collect.router, tags=["Collector"])
