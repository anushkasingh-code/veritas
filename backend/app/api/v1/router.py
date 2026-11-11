"""
API v1 Router aggregating all v1 feature routers.
"""

from fastapi import APIRouter

from app.api.v1 import analyze, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analyze.router, tags=["Research Analysis"])
