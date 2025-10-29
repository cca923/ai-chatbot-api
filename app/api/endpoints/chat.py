from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.services.sse_service import sse_event_generator

# Create a new router for chat endpoints
router = APIRouter()


@router.get("/ask")
async def get_ask(request: Request):
    """
    The main SSE route.
    The final URL will be /api/chat/ask
    """
    print("Client connected to /api/chat/ask")
    event_generator = sse_event_generator(request)
    return EventSourceResponse(event_generator)
