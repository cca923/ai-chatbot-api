import asyncio
import httpx
from ddgs import DDGS
from readability import Document
import trafilatura
from typing import List, Dict, Optional


# We define a User-Agent header to pretend we are a real browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


async def scrape_url_content(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """
    Asynchronously scrape content from a single URL.
    Uses readability-lxml and trafilatura as a fallback.
    """
    try:
        response = await client.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers=BROWSER_HEADERS,
        )

        response.raise_for_status()

        doc = Document(response.text)
        content_html = doc.summary(html_partial=True)

        if not content_html or len(content_html) < 100:
            content_text = trafilatura.extract(response.text)
            if content_text:
                return content_text

        return content_html

    except httpx.HTTPStatusError as e:
        print(f"HTTP error scraping {url}: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Network error scraping {url}: {e}")
    except Exception as e:
        print(f"Error scraping {url}: {e}")

    return None


async def search_and_scrape(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo, then concurrently scrape the results.
    """
    search_results = []

    try:
        print(f"Searching for: {query}")
        # We wrap the sync call in asyncio.to_thread
        search_results = await asyncio.to_thread(
            DDGS().text,
            query=query,
            max_results=max_results,
        )
        if not search_results:
            print("No search results found.")
            return []

    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []

    print(f"Found {len(search_results)} results. Starting scrape...")
    final_data = []

    # We can also set default headers for the entire client
    async with httpx.AsyncClient(headers=BROWSER_HEADERS) as client:
        tasks = [
            scrape_url_content(client, result["href"]) for result in search_results
        ]
        scraped_contents = await asyncio.gather(*tasks, return_exceptions=True)

    for search_result, content_or_error in zip(search_results, scraped_contents):
        if isinstance(content_or_error, str) and content_or_error:
            final_data.append(
                {
                    "url": search_result["href"],
                    "title": search_result["title"],
                    "content": content_or_error,
                }
            )
        else:
            print(f"Failed to scrape {search_result['href']}: {content_or_error}")

    print(f"Successfully scraped {len(final_data)} of {len(search_results)} pages.")
    return final_data
