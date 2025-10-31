import asyncio
from ddgs import DDGS
from typing import List, Dict, Any


async def search_and_get_snippets(
    query: str, max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Performs a DuckDuckGo search and returns a list of snippets.
    This is the optimized version that AVOIDS scraping.
    """
    print(f"WEB SEARCH: Searching snippets for '{query}'...")

    try:
        # Use asyncio.to_thread to run the blocking search in a separate thread
        # We must use query=query, not keywords=query, for the new 'ddgs' package
        results_list = await asyncio.to_thread(
            DDGS().text, query=query, max_results=max_results
        )

        if not results_list:
            print("WEB SEARCH: No results found from DDGS.")
            return []

        # Format the results
        snippets = []
        for r in results_list:
            # DDGS returns 'title', 'href', 'body'
            # 'body' is the snippet we want
            if r.get("body"):  # Only include if snippet (body) exists
                snippets.append(
                    {
                        "title": r.get("title", "No Title"),
                        "url": r.get("href", ""),
                        "content": r.get("body"),  # This is the snippet
                    }
                )

        print(f"WEB SEARCH: Found {len(snippets)} snippets.")
        return snippets

    except Exception as e:
        print(f"WEB SEARCH: Error during snippet search: {e}")
        return []
