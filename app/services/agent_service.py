import re
import asyncio
import json
from google import generativeai as genai
from app.core.config import settings
from app.services.web_search import search_and_get_snippets
from typing import AsyncGenerator, Dict, Any

# --- Configure Gemini ---
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError as e:
    print(f"Error: GEMINI_API_KEY not configured. {e}")
except Exception as e:
    print(f"An unexpected error occurred during genai configuration: {e}")


# --- Agents ---
async def _run_planner(query: str, model_name: str) -> list[str]:
    """
    Phase 1: The Planner agent generates search queries based on the user's query.
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
        json_str = response.text.strip().lstrip("```json").lstrip("```").rstrip("```")
        print(f"AGENT (Planner): Raw response: \n{json_str}")
        search_queries = json.loads(json_str)
        print(f"AGENT (Planner): Generated queries: {search_queries}")
        return search_queries
    except Exception as e:
        print(f"AGENT (Planner): Error - {e}")
        return [query]  # Fallback to original query


async def _run_researcher(search_queries: list[str]) -> tuple[str, list[dict]]:
    """
    Phase 2: The Researcher agent fetches snippets for the queries.
    """
    print(f"AGENT (Researcher): Initializing...")
    tasks = [search_and_get_snippets(q, max_results=2) for q in search_queries]
    results_lists = await asyncio.gather(*tasks)

    all_snippets = []
    context_str = ""
    source_id_counter = 1
    seen_urls = set()

    for results in results_lists:
        for res in results:
            if res["url"] not in seen_urls:
                seen_urls.add(res["url"])
                snippet_data = {
                    "id": source_id_counter,
                    "url": res["url"],
                    "title": res["title"],
                    "content": res["content"],
                }
                all_snippets.append(snippet_data)
                context_str += f"[Source {source_id_counter}]:\n"
                context_str += f"URL: {res['url']}\n"
                context_str += f"Title: {res['title']}\n"
                context_str += f"Snippet: {res['content']}\n\n"
                source_id_counter += 1

    print(f"AGENT (Researcher): Found {len(all_snippets)} unique snippets.")
    return context_str, all_snippets


async def _run_writer(
    query: str, context_str: str, model_name: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Phase 3: The Writer agent generates a streaming answer based on the context.
    This is an async generator.
    """
    print(f"AGENT (Writer): Initializing with model {model_name}...")
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    You are an expert AI assistant. Your task is to answer the user's query based *only* on the provided sources (snippets).
    Do not use any prior knowledge.

    Here are the provided source snippets:
    <Sources>
    {context_str}
    </Sources>

    User Query: "{query}"
    
    Instructions:
    1.  Read the User Query and the Provided Sources.
    2.  Synthesize a clear, concise, and helpful answer to the query using *only* the information in the <Sources>.
    3.  If the <Sources> do not contain enough information, state "I'm sorry, but the provided search results do not contain enough information to answer this question."
    4.  You **MUST** cite the sources you use. Citations MUST be placed *immediately* after the information they support.
    5.  **CRITICAL**: Citations MUST be formatted as Markdown anchor links: `[<source_id>](#citation-<source_id>)`.
    6.  Your answer must be in Markdown format.

    EXAMPLE:
    ...the sky is blue [1](#citation-1). AI is a complex field [2](#citation-2).

    Now, generate the answer based *only* on the <Sources> provided.
    """

    try:
        # Use stream=True to get chunks
        stream = await model.generate_content_async(prompt, stream=True)

        async for chunk in stream:
            if chunk.text:
                text_chunk = chunk.text
                # Fix mixed brackets around citation links: (#citation-1], [#citation-1), or [#citation-1] -> (#citation-1)
                text_chunk = re.sub(
                    r"[\[\(]#citation-(\d+)[\]\)]", r"(#citation-\1)", text_chunk
                )
                # Remove extra spaces between citation ID and link: [1] (#citation-1) -> [1](#citation-1)
                text_chunk = re.sub(
                    r"\[(\d+)\]\s+\(#citation-", r"[\1](#citation-", text_chunk
                )
                yield {"event": "chunk", "data": text_chunk}

        print(f"AGENT (Writer): Finished streaming answer.")

    except Exception as e:
        print(f"AGENT (Writer): Error - {e}")
        yield {"event": "error", "data": f"An error occurred in the Writer agent: {e}"}


# --- Orchestrator ---
async def run_agent_workflow(
    query: str,
) -> AsyncGenerator[Dict[str, Any], None]:
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
        yield {"event": "trace", "data": "Planning..."}
        search_queries = await _run_planner(query, PLANNER_MODEL)

        # === PHASE 2: RESEARCHER ===
        yield {"event": "trace", "data": "Searching..."}
        context_str, sources = await _run_researcher(search_queries)

        # === PHASE 2.5: YIELD SOURCES ===
        # Send sources to frontend *before* writing the answer
        yield {"event": "sources", "data": json.dumps(sources)}

        # === PHASE 3: WRITER ===
        yield {"event": "trace", "data": "Reading and Writing..."}

        if not context_str:
            yield {"event": "trace", "data": "No relevant snippets found."}
            yield {
                "event": "chunk",
                "data": "I could not find any relevant information to answer your query.",
            }
        else:
            # We yield 'chunk' events for the streaming answer
            async for event in _run_writer(query, context_str, WRITER_MODEL):
                yield event  # Pass the event (chunk or error) through

        # === PHASE 4: DONE ===
        print("--- WORKFLOW COMPLETE ---")
        yield {"event": "done", "data": "Stream complete."}

    except Exception as e:
        print(f"--- WORKFLOW FAILED ---")
        print(f"An unexpected error occurred in the workflow: {e}")
        yield {"event": "error", "data": f"An unexpected workflow error occurred: {e}"}
        yield {"event": "done", "data": "Stream failed."}
