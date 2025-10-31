import asyncio
import json
from google import generativeai as genai
from app.core.config import settings
from app.services.web_search import search_and_get_snippets  # D7.6 optimization
from typing import AsyncGenerator, Dict, Any

# --- Configure Gemini ---
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError as e:
    print(f"Error: GEMINI_API_KEY not configured. {e}")
except Exception as e:
    print(f"An unexpected error occurred during genai configuration: {e}")


# --- Refactor: Planner Agent ---
async def _run_planner(query: str, model_name: str) -> list[str]:
    """
    Phase 1: The Planner agent generates search queries based on the user's query.
    (This is run by the D7.5 refactored service)
    """
    print(f"AGENT (Planner): Initializing with model {model_name}...")

    model = genai.GenerativeModel(model_name)

    planner_prompt = f"""
    You are an expert search query planner.
    The user's query is: "{query}"
    
    Please generate 2-3 concise, high-quality search queries that will help answer the user's query.
    Return *only* a JSON array of strings.
    
    Example:
    [
      "query 1",
      "query 2",
      "query 3"
    ]
    """

    try:
        response = await model.generate_content_async(planner_prompt)

        # Clean the response to get only the JSON part
        json_str = response.text.strip().lstrip("```json").lstrip("```").rstrip("```")
        print(f"AGENT (Planner): Raw response: \n{json_str}")

        search_queries = json.loads(json_str)
        print(f"AGENT (Planner): Generated queries: {search_queries}")
        return search_queries

    except json.JSONDecodeError as e:
        print(f"AGENT (Planner): Error - Failed to decode JSON: {e}")
        # Fallback: use the original query
        return [query]
    except Exception as e:
        print(f"AGENT (Planner): Error - {e}")
        # Fallback: use the original query
        return [query]


# --- Refactor: Researcher Agent ---
async def _run_researcher(search_queries: list[str]) -> tuple[str, list[dict]]:
    """
    Phase 2: The Researcher agent fetches snippets for the queries.
    It uses the D7.6 optimized 'search_and_get_snippets' service.
    """
    print(f"AGENT (Researcher): Initializing...")

    # Create concurrent tasks for all search queries
    tasks = [search_and_get_snippets(q, max_results=2) for q in search_queries]

    # Run all search tasks concurrently
    results_lists = await asyncio.gather(*tasks)

    # Flatten the list of lists and prepare context
    all_snippets = []
    context_str = ""
    source_id_counter = 1

    # We use a set to avoid duplicate URLs
    seen_urls = set()

    for results in results_lists:
        for res in results:
            if res["url"] not in seen_urls:
                seen_urls.add(res["url"])

                snippet_data = {
                    "id": source_id_counter,
                    "url": res["url"],
                    "title": res["title"],
                    "content": res["content"],  # This is the snippet
                }
                all_snippets.append(snippet_data)

                # Format for the AI's context
                context_str += f"[Source {source_id_counter}]:\n"
                context_str += f"URL: {res['url']}\n"
                context_str += f"Title: {res['title']}\n"
                context_str += f"Snippet: {res['content']}\n\n"

                source_id_counter += 1

    print(f"AGENT (Researcher): Found {len(all_snippets)} unique snippets.")
    return context_str, all_snippets


async def _run_writer(query: str, context_str: str, model_name: str):
    """
    Phase 3: The Writer agent generates a streaming answer based on the context.
    """
    print(f"AGENT (Writer): Initializing with model {model_name}...")

    model = genai.GenerativeModel(model_name)

    writer_prompt = f"""
    You are an expert AI assistant. Your task is to answer the user's query based *only* on the provided sources.
    Do not use any prior knowledge.
    The user's query is: "{query}"

    Here are the relevant source snippets:
    ---
    {context_str}
    ---

    Please provide a concise, factual answer to the user's query.
    
    **CRITICAL: CITATION FORMAT**:
    1.  You MUST cite *every* piece of information you use.
    2.  Citations MUST be in the **exact** Markdown link format: `[1](#citation:1)`, `[2](#citation:2)`, etc.
    3.  If a sentence is synthesized from multiple sources, cite all of them, e.g., `[1](#citation:1)[2](#citation:2)`.

    **Good Example (This is what you MUST do):**
    The sky is blue [1](#citation:1). It is also high up [1](#citation:1)[2](#citation:2).

    **Bad Example (DO NOT do this):**
    The sky is blue [1].
    
    **Bad Example (DO NOT do this):**
    The sky is blue 1.

    Now, please answer the query based *only* on the provided sources.
    """

    try:
        # We use stream=True to get chunks
        stream = await model.generate_content_async(writer_prompt, stream=True)

        async for chunk in stream:
            if chunk.text:
                # Yield each text chunk as it arrives
                yield chunk.text

        print(f"AGENT (Writer): Finished streaming.")

    except Exception as e:
        print(f"AGENT (Writer): Error - {e}")
        # Yield a user-facing error message
        yield f"\n\n[Error] An error occurred while generating the answer: {e}"


# --- Refactor: Orchestrator ---
async def run_agent_workflow(query: str):
    """
    The main orchestrator that runs the full Planner -> Researcher -> Writer workflow.
    This is what the 'chat.py' endpoint calls.
    It yields events for the SSE stream.
    """
    print(f"--- WORKFLOW STARTED (Query: {query}) ---")

    PLANNER_MODEL = "gemini-2.0-flash"
    WRITER_MODEL = "gemini-2.0-flash"

    try:
        # === PHASE 1: PLANNER ===
        yield {"event": "trace", "data": "Phase 1: Planning..."}
        search_queries = await _run_planner(query, PLANNER_MODEL)

        # === PHASE 2: RESEARCHER ===
        yield {"event": "trace", "data": "Phase 2: Searching..."}
        context_str, sources = await _run_researcher(search_queries)

        # === PHASE 2.5: YIELD SOURCES ===
        # Send sources to frontend *before* writing the answer
        yield {"event": "sources", "data": json.dumps(sources)}

        # === PHASE 3: WRITER ===
        yield {"event": "trace", "data": "Phase 3: Reading and Writing..."}

        # Check if context is empty
        if not context_str:
            yield {"event": "trace", "data": "No relevant snippets found."}
            yield {
                "event": "chunk",
                "data": "I could not find any relevant information to answer your query.",
            }
        else:
            # We yield 'chunk' events for the streaming answer
            async for chunk in _run_writer(query, context_str, WRITER_MODEL):
                yield {"event": "chunk", "data": chunk}

        # === PHASE 4: DONE ===
        print("--- WORKFLOW COMPLETE ---")
        yield {"event": "done", "data": "Stream complete."}

    except Exception as e:
        print(f"--- WORKFLOW FAILED ---")
        print(f"An unexpected error occurred in the workflow: {e}")
        yield {"event": "error", "data": f"An unexpected workflow error occurred: {e}"}
        yield {"event": "done", "data": "Stream failed."}
