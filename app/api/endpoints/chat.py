from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.services.sse_service import search_event_generator

router = APIRouter()


@router.get("/ask")
async def get_ask(request: Request, query: str):
    """
    The main SSE route.
    It now accepts a 'query' parameter from the URL.
    """
    if not query:
        return {"error": "Query parameter is required."}

    print(f"Client connected to /api/chat/ask with query: '{query}'")

    event_generator = search_event_generator(request, query)

    return EventSourceResponse(event_generator)
