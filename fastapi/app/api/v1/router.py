"""API v1 Router"""
from fastapi import APIRouter

from app.api.v1 import users, interviews, evaluations, tasks, recommendations, learning, tts, career

# Create API v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(users.router)
api_router.include_router(interviews.router)
api_router.include_router(evaluations.router)
api_router.include_router(tasks.router)
api_router.include_router(recommendations.router)
api_router.include_router(learning.router)
api_router.include_router(tts.router)
api_router.include_router(career.router)

__all__ = ["api_router"]
