import asyncio
import json
from app.core.config import settings


# This is the "mock" AI service, simulates AI thinking and streaming
async def run_agent_workflow(query: str):
    """
    Runs the MOCK AI agent workflow and yields events.
    In D7, this will be replaced with real AutoGen + Gemini calls.
    """
    print(f"Initializing MOCK AI Agent workflow for query: {query}")

    # Simulate Gemini API Key check
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not set!")
        # Yield an 'error' event
        yield {"event": "error", "data": "GEMINI_API_KEY is not set on the server."}
        return  # Return early

    try:
        # --- Mock Phase 1: Planning ---
        # Simulate AI thinking (e.g., Planner Agent is working)
        await asyncio.sleep(0.5)
        yield {"event": "trace", "data": "Planning..."}

        # --- Mock Phase 2: Thinking & Writing ---
        await asyncio.sleep(1.0)  # Simulate a longer thinking time
        yield {"event": "trace", "data": "Thinking... (Mock)"}

        # --- Mock Phase 3: Streaming Chunks ---
        # Simulate AI streaming word-by-word (e.g., Writer Agent is working)
        mock_response = "This is a simulated AI response."
        for char in mock_response:
            yield {"event": "chunk", "data": char}
            await asyncio.sleep(0.02)  # Simulate typing speed

        # --- Mock Phase 4: Done ---
        await asyncio.sleep(0.5)
        yield {"event": "done", "data": "Mock stream complete."}

    except asyncio.CancelledError:
        # This is the standard error FastAPI raises when the client disconnects
        print("Stream cancelled by client (agent_service).")
        raise

    except Exception as e:
        # Handle any other unexpected errors
        print(f"An error occurred in agent_service: {e}")
        yield {"event": "error", "data": f"An internal server error occurred: {e}"}
    finally:
        # After this generator ends, sse-starlette will automatically close the connection
        print("Closing AI agent workflow stream.")
