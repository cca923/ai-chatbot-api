import asyncio
import google.generativeai as genai
import json
from typing import AsyncGenerator, List, Dict, Any, Union
from app.services.web_search import search_and_get_snippets
from app.core.config import settings

# Configure the Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)


# --- Private Agent Functions ---
async def _run_planner(query: str) -> List[str]:
    """
    Phase 1: Planner Agent (Gemini)
    Takes the user query and generates a list of search queries.
    """
    print("AGENT (Planner): Initializing...")

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    You are an expert search query planner.
    Based on the user's query: "{query}"
    
    Please generate a list of 2-3 concise search queries that will help answer the user's question.
    
    Return your answer ONLY as a JSON list.
    Example: ["query 1", "query 2", "query 3"]
    """

    try:
        response = await model.generate_content_async(prompt)

        # Clean the response and parse JSON
        cleaned_response = (
            response.text.strip().replace("```json", "").replace("```", "")
        )
        print(f"AGENT (Planner): Raw response: {cleaned_response}")

        search_queries = json.loads(cleaned_response)

        if isinstance(search_queries, list) and all(
            isinstance(q, str) for q in search_queries
        ):
            print(f"AGENT (Planner): Generated queries: {search_queries}")
            return search_queries
        else:
            raise ValueError("Response was not a list of strings.")

    except Exception as e:
        print(f"AGENT (Planner): Error - {e}. Defaulting to user query.")
        # Fallback in case JSON parsing fails
        return [query]


async def _run_researcher(
    search_queries: List[str],
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Phase 2: Researcher Agent
    Takes search queries, fetches snippets, and prepares context.
    """
    print("AGENT (Researcher): Initializing...")

    # We run searches concurrently for speed
    tasks = [search_and_get_snippets(q, max_results=2) for q in search_queries]
    results_lists = await asyncio.gather(*tasks)

    all_snippets = [
        item for sublist in results_lists for item in sublist
    ]  # Flatten the list

    # De-duplicate snippets based on URL
    unique_snippets = []
    seen_urls = set()
    for idx, snippet in enumerate(all_snippets):
        if snippet["url"] not in seen_urls:
            snippet["id"] = idx + 1  # Assign a unique ID
            unique_snippets.append(snippet)
            seen_urls.add(snippet["url"])

    print(f"AGENT (Researcher): Found {len(unique_snippets)} unique snippets.")

    # Prepare context string for the Writer
    context_str = ""
    for s in unique_snippets:
        context_str += f"[Source {s['id']}]\nURL: {s['url']}\nTitle: {s['title']}\nSnippet: {s['content']}\n\n"

    return {"context_string": context_str, "sources_list": unique_snippets}


async def _run_writer(
    query: str, context_string: str
) -> AsyncGenerator[Dict[str, str], None]:
    """
    Phase 3: Writer Agent (Gemini Streaming)
    Reads the context and streams the final answer.
    """
    print("AGENT (Writer): Initializing...")

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    You are an expert AI assistant. Your task is to answer the user's query based *only* on the provided sources.
    Do not use any prior knowledge.
    
    User Query: "{query}"
    
    Provided Sources (Snippets):
    ---
    {context_string}
    ---
    
    Instructions:
    1.  Read the User Query and the Provided Sources.
    2.  Synthesize a comprehensive answer to the query.
    3.  You **MUST** cite the sources you use.
    4.  Cite sources using the format [1], [2], etc., based on the [Source n] tag.
    5.  If the snippets do not contain enough information to answer the query, state that clearly.
    6.  Do not make up information.
    7.  Your answer must be in Markdown format.
    """

    try:
        # We use stream=True to get chunks
        stream = await model.generate_content_async(prompt, stream=True)

        async for chunk in stream:
            if chunk.parts:
                # print(f"AGENT (Writer): Yielding chunk: {chunk.text[:20]}...")
                yield {"event": "chunk", "data": chunk.text}

    except Exception as e:
        print(f"AGENT (Writer): Error - {e}")
        # Yield an error event to the client
        yield {"event": "error", "data": f"Error during AI generation: {e}"}


# --- Public Orchestrator Function ---
async def run_agent_workflow(query: str) -> AsyncGenerator[Dict[str, str], None]:
    """
    This is the main orchestrator for the agent workflow.
    It calls Planner -> Researcher -> Writer and yields events.
    """
    print(f"\n--- WORKFLOW STARTED (Query: {query}) ---")

    try:
        # === PHASE 1: PLANNER ===
        yield {"event": "trace", "data": "Phase 1: Planning..."}
        search_queries = await _run_planner(query)

        # === PHASE 2: RESEARCHER (Snippet Version) ===
        yield {
            "event": "trace",
            "data": f"Phase 2: Searching for {len(search_queries)} queries...",
        }
        research_data = await _run_researcher(search_queries)
        context_string = research_data["context_string"]
        sources_list = research_data["sources_list"]

        # === PHASE 2.5: YIELD SOURCES ===
        # Send sources to frontend *before* writing
        yield {"event": "sources", "data": json.dumps(sources_list)}

        # === PHASE 3: WRITER ===
        yield {
            "event": "trace",
            "data": "Phase 3: Reading snippets and writing answer...",
        }

        if not context_string:
            # Handle case where no snippets were found
            yield {
                "event": "chunk",
                "data": "I'm sorry, I couldn't find any relevant snippets to answer your question.",
            }
        else:
            # Stream the writer's response
            async for event in _run_writer(query, context_string):
                yield event  # Pass the chunk or error event up

        # === PHASE 4: DONE ===
        print("--- WORKFLOW COMPLETE ---")
        yield {"event": "done", "data": "Stream complete."}

    except Exception as e:
        print(f"--- WORKFLOW FAILED: {e} ---")
        yield {
            "event": "error",
            "data": f"An unexpected error occurred in the workflow: {e}",
        }
