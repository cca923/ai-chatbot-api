import asyncio
import json
from fastapi import Request
from app.services.web_search import search_and_scrape


async def search_event_generator(request: Request, query: str):
    """
    The updated SSE generator for D4.
    It now yields specific event names and a 'done' event.
    """
    try:
        # 1. Yield a 'search' event
        yield {
            "event": "search",
            "data": f"Searching the web for: '{query}'...",
        }

        scraped_data = await search_and_scrape(query, max_results=3)

        if not scraped_data:
            yield {
                "event": "error",
                "data": "No content could be scraped.",
            }
            return

        # 2. Yield a 'sources' event
        source_list = [
            {"url": item["url"], "title": item["title"]} for item in scraped_data
        ]
        yield {
            "event": "sources",
            "data": json.dumps(source_list),
        }

        # 3. Yield 'content' snippets (simulating reading)
        for i, item in enumerate(scraped_data):
            event_data = {
                "source_index": i,
                "content_snippet": item["content"][:250] + "...",
            }
            yield {
                "event": "content",
                "data": json.dumps(event_data),
            }
            await asyncio.sleep(0.5)

        # 4. Yield a 'done' event to cleanly close the stream
        yield {"event": "done", "data": "Stream complete"}

    except asyncio.CancelledError:
        print("Stream cancelled by client.")
    except Exception as e:
        print(f"An error occurred in SSE generator: {e}")
        yield {"event": "error", "data": f"An internal error occurred: {e}"}
    finally:
        print("Closing stream.")
