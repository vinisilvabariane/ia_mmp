from fastapi import APIRouter

from app.controllers.health_controller import router as health_router
from app.controllers.route_controller import router as route_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(route_router, tags=["routes"])
