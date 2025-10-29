from fastapi import APIRouter
from app.api.endpoints import chat

# This router combines all endpoint routers under /api
api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
