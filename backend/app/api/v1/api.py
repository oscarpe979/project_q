from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, schedules, upload

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(schedules.router, tags=["schedules"])
api_router.include_router(upload.router, tags=["upload"])
