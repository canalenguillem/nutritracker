from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.exercises import router as exercises_router
from app.api.v1.health import router as health_router
from app.api.v1.meals import router as meals_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(meals_router)
router.include_router(exercises_router)
