# Insight AI - Backend API

This is the backend service for the **Insight AI** search assistant. It’s built with **FastAPI** and **Google Gemini**, implementing a Perplexity-like multi-agent Q&A workflow.

You can check the [Live API Endpoint](https://ai-chatbot-api-lxkd.onrender.com) here.

---

# System Architecture

## Key Technologies

- **FastAPI**: A high-performance, asynchronous Python framework used to build the API and handle concurrent SSE connections.

- **Server-Sent Events (SSE)**: Used via `sse-starlette` to push real-time, named events (`trace`, `sources`, `chunk`) to the client.

- **Gemini (Google AI)**: `gemini-2.0-flash` is used for all LLM tasks (Planner and Writer) via `generate_content_async` (including streaming).

- **DDGS (DuckDuckGo Search)**: A free, no-API-key library used to fetch real-time web snippets.

## Project Structure

```
ai-chatbot-api/
├── app/                     # Main application source code
│   ├── api/                 # API routing definitions
│   │   ├── endpoints/       # Individual endpoint logic (e.g., chat.py)
│   │   └── router.py        # Combines all endpoint routers
│   ├── core/                # Core configuration
│   │   └── config.py        # Pydantic settings, loads .env (GEMINI_API_KEY, CORS)
│   ├── services/            # Business logic
│   │   ├── agent_service.py # Multi-agent workflow (Planner, Researcher, Writer)
│   │   └── web_search.py    # DDGS snippet-fetching service
│   └── main.py              # FastAPI entry point, registers middleware & routers
├── .env.example             # Example environment file
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── run.py                   # Server launcher (for local dev & Render deployment)
```

---

# Core Features

## Agent Roles

The system follows a **three-phase multi-agent workflow** with a Planner, Researcher, and Writer coordinated by an Orchestrator.
Their individual roles are summarized in the table below.

| Agent            | Implementation (`agent_service.py`) | Description                       | Key Responsibilities                                                                                                                                               |
| ---------------- | ----------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Planner**      | `_run_planner`                      | Query decomposition expert        | Analyzes the user’s question and generates 2–3 optimized search queries to guide retrieval.                                                                        |
| **Researcher**   | `_run_researcher`                   | Web retriever and context builder | Uses the generated search queries to fetch snippets via `search_and_get_snippets()`, merges unique sources, and constructs a context string for citation.          |
| **Writer**       | `_run_writer`                       | Response synthesizer              | Reads the aggregated snippets and produces a structured, markdown-formatted answer **with live streaming** and **inline citations**.                               |
| **Orchestrator** | `run_agent_workflow`                | Workflow controller               | Sequentially triggers Planner → Researcher → Writer, handles error recovery, and streams events (`trace`, `sources`, `chunk`, `done`) to the frontend through SSE. |

## SSE Event Format

The backend sends the following named events to the frontend:

| Event     | Example (`data`)          | Purpose                                                        |
| --------- | ------------------------- | -------------------------------------------------------------- |
| `trace`   | `Planning...`             | Displays progress updates in the UI.                           |
| `sources` | `[{...}]`                 | Sent before the AI writes, allowing source cards to render.    |
| `chunk`   | `Partial streamed answer` | The token-by-token stream of the AI's answer.                  |
| `error`   | `An error occurred...`    | Forwards backend errors to the frontend UI.                    |
| `done`    | `Stream complete.`        | Notifies the client that the stream has finished successfully. |

---

# Setup Instructions

## Step 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3. Set up environment variables

Copy `.env.example` to `.env` and fill in the configurations:

```bash
cp .env.example .env
```

## Step 4. Start the local server

The server will run on `http://localhost:8000`.

```bash
python run.py
```
