"""HTTP API for the agent. POST /ask streams each step as it happens.

    make api    (uvicorn --factory backend.api.main:create_app --reload --port 8000)

Streaming uses Server-Sent Events: plain text over one HTTP response, one
event per graph step, then a final "result" event. It is one-way (server to
browser), which is all "show the steps live" needs, so no WebSocket.
"""
import json
import sys
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agent.graph import build_graph
from backend.agent.warmup import needs_warm_up, warm_up
from backend.formatting import describe_step, json_value
from backend.llm import LLM, get_llm
from backend.warehouse import Warehouse, get_warehouse

# Clickable example chips in the UI. Olist questions that cover each chart type.
EXAMPLE_QUESTIONS = [
    "How many orders were delivered?",
    "Which 5 customer states generated the most revenue?",
    "How many orders were placed each month in 2017?",
    "What are the top 5 product categories by revenue?",
    "Do late deliveries get worse reviews?",
]

FRONTEND_ORIGIN = "http://localhost:3000"  # the Next.js dev server


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def create_app(llm: LLM | None = None, warehouse: Warehouse | None = None) -> FastAPI:
    """Build the app. Tests pass a fake LLM; normally both come from .env."""
    llm = llm or get_llm()
    warehouse = warehouse or get_warehouse()
    agent = build_graph(llm, warehouse)
    # One question at a time: all requests share one DuckDB connection, and a
    # local model answers one request at a time anyway. Fine for a demo.
    lock = threading.Lock()
    status = {"ready": not needs_warm_up(llm)}

    def warm() -> None:
        # Holds the lock, so a question asked during warm-up waits for it
        # instead of competing with it for the local model.
        with lock:
            try:
                warm_up(llm, warehouse)
            except Exception as e:  # e.g. Ollama not running; questions will report it
                print(f"[api] warm-up failed: {type(e).__name__}: {e}", file=sys.stderr)
            status["ready"] = True

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not status["ready"]:
            # Background thread: the server accepts requests immediately.
            threading.Thread(target=warm, daemon=True).start()
        yield

    app = FastAPI(
        title="QueryPilot", description="Ask questions about your data in plain English.", lifespan=lifespan
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=[FRONTEND_ORIGIN], allow_methods=["GET", "POST"], allow_headers=["*"]
    )

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "ready": status["ready"],
            "model": llm.name,
            "dataset": warehouse.dataset,
            "warehouse": warehouse.dialect,  # "duckdb" or "snowflake"
        }

    @app.get("/examples")
    def examples() -> dict:
        return {"questions": EXAMPLE_QUESTIONS}

    @app.post("/ask")
    def ask(request: AskRequest) -> StreamingResponse:
        return StreamingResponse(
            _stream_answer(agent, lock, request.question, llm.name),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},  # don't buffer the stream
        )

    return app


def _stream_answer(agent, lock: threading.Lock, question: str, model: str):
    """Yield one SSE event per graph step, then the full result."""
    with lock:
        state = {"question": question}
        start = time.time()
        config = {"run_name": "api question", "tags": ["api"], "metadata": {"model": model}}
        try:
            for update in agent.stream(state, config=config, stream_mode="updates"):
                for node, changes in update.items():
                    state.update(changes)
                    yield _event("step", {
                        "node": node,
                        "detail": describe_step(node, changes),
                        "error": bool(changes.get("error")),
                        "elapsed_s": round(time.time() - start, 2),
                    })
        except Exception as e:  # e.g. the LLM server is down; tell the UI instead of hanging
            yield _event("error", {"message": f"{type(e).__name__}: {e}"})
            return

        failed = bool(state.get("error"))
        yield _event("result", {
            "question": question,
            "answer": state.get("answer", ""),
            "sql": state.get("sql", ""),  # guardrail 7: always show the SQL that ran
            "columns": [] if failed else state.get("columns", []),
            "rows": [] if failed else state.get("rows", []),
            "chart": None if failed else state.get("chart"),
            "error": state.get("error", ""),
            "repairs": state.get("attempts", 0),
            "input_tokens": state.get("input_tokens", 0),
            "output_tokens": state.get("output_tokens", 0),
            "elapsed_s": round(time.time() - start, 2),
            "model": model,
        })


def _event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=json_value)}\n\n"
