# Backend AI Prompt Log

This project was completed with the assistance of an AI Code Agent.
Below are the key prompts that guided the AI in backend architecture design, feature development, and debugging.

---

### 1. Scoping: Defining the MVP

**Prompt:**

> I have a detailed 14-day plan (including `rapidfuzz` for precise citations, multiple search APIs, `/metrics` endpoints, etc.). This is too complex for a two-week project. What parts can we remove to get a working MVP first?

**Outcome:**
We collectively decided on a simplified MVP — removing `rapidfuzz`, the `/metrics` endpoint, and all extra APIs (keeping only DDGS).
This finalized the project’s core scope and ensured timely delivery.

### 2. Architecture: Professional Backend Structure

**Prompt:**

> I don’t want a single `main.py` file. I want a professional FastAPI structure using api, core, services, and routes.

**Outcome:**
The backend was refactored into a modular, multi-folder structure, improving clarity and maintainability.

### 3. Architecture: Responsibility Separation

**Prompt:**

> Is putting all the logic (Planner, Researcher, Writer) into one giant function in `run_agent_workflow` good practice? Shouldn’t these roles be split into separate functions?

**Outcome:**
`agent_service.py` was refactored into smaller functions (`_run_planner`, `_run_researcher`, `_run_writer`), greatly improving readability and modularity.

### 4. Architecture: Chat History Decision

**Prompt:**

> I want to upgrade to a chat UI, but I don’t want the backend to handle history, that’s too complex (requires a database and sessions).

**Outcome:**
We implemented a **Stateful UI** (frontend chat history) and a **Stateless Backend API** (one-shot query), keeping the backend lightweight and scalable.

### 5. Debugging & Optimization: Fixing 429 Error

**Prompt:**

> The Writer agent is getting an `Error 429: Resource exhausted`.

**Outcome:**
The issue was likely caused by the full-text scraper (`readability-lxml`) sending excessive content to Gemini. We switched to using only the snippets provided by DDGS, and `web_search.py` was rewritten to a snippet-only version. The 429 error was resolved, and Phase 2 (search) performance improved significantly.

### 6. Debugging: Citation Format Consistency

**Prompt:**

> The Writer agent is still inconsistent. It sometimes outputs `[1]`, `(1)`, or `[1, 3]` instead of properly formatted citations like `[1](#citation-1)`.

**Outcome:**
The Writer prompt in `agent_service.py` was refined with explicit **correct vs. incorrect citation examples** to guide model behavior. A **regex-based post-processing step** was added to normalize citation output, and this logic was later migrated to `app/utils/citation_utils.py` for better reusability.
