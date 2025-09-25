"""
API Router for AI Measurement Service
"""

from fastapi import APIRouter
from .endpoints import measurements, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])