from fastapi import APIRouter, Request, Query
from sse_starlette.sse import EventSourceResponse
from app.services.agent_service import run_agent_workflow

router = APIRouter()


@router.get("/ask")
async def get_ask(
    request: Request,
    query: str = Query(..., description="The user's query"),
):
    """
    Main SSE endpoint that streams the AI agent's workflow.
    It directly calls the agent service which is an async generator.
    """
    print(f"Client connected to /api/chat/ask with query: '{query}'")

    event_generator = run_agent_workflow(query)
    # Wrap the generator with SSE formatting
    return EventSourceResponse(event_generator)
