from fastapi import APIRouter
from app.api.v1.posts import router as posts_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(posts_router)

__all__ = ["api_v1_router"]
