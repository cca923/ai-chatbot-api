import asyncio
from fastapi import Request


async def sse_event_generator(request: Request):
    """
    This is our asynchronous generator function for SSE.
    It will yield a message every 0.5 seconds for this test.
    """
    stream_count = 0
    try:
        while True:
            # Check if the client has disconnected
            if await request.is_disconnected():
                print("Client disconnected.")
                break

            # This is the data we send.
            yield {"event": "message", "data": f"ping {stream_count}"}  # The event name

            stream_count += 1
            await asyncio.sleep(0.5)  # Wait 0.5 seconds

    except asyncio.CancelledError:
        print("Stream cancelled by client.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"Closing stream after {stream_count} pings.")
