"""MCP server: QueryPilot's tools for any MCP client (Claude Desktop, Claude Code, ...).

    python -m backend.mcp_server        (or: make mcp)

Runs over stdio: the client starts this process and talks to it through
stdin/stdout, so nothing here may print to stdout.

Tools:
  list_tables     tables with a one-line business description
  describe_table  columns, types, business notes, sample rows
  run_query       one read-only SELECT, behind the same guardrails as the agent
  ask             the full QueryPilot agent: semantic layer, repair loop, summary

`run_query` lets the calling assistant write its own SQL, which skips the
semantic layer's business definitions (e.g. revenue excludes freight). The
tool descriptions steer business questions to `ask` for that reason.
"""
import logging
import os
import threading
from functools import lru_cache
from pathlib import Path

# The client may launch this from any folder; relative paths in .env
# (data/, .secrets/) are relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)

from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

from backend.agent import semantic  # noqa: E402
from backend.agent.graph import build_graph  # noqa: E402
from backend.agent.warmup import needs_warm_up, warm_up  # noqa: E402
from backend.formatting import json_value  # noqa: E402
from backend.guardrails.sql_validator import validate_sql  # noqa: E402
from backend.llm import LLM, get_llm  # noqa: E402
from backend.warehouse import QueryTimeoutError, Warehouse, get_warehouse  # noqa: E402

MAX_ROWS_RETURNED = 100  # keep tool results small for the calling model
WAREHOUSE_NAME = os.getenv("WAREHOUSE", "duckdb").lower()

server = MCPServer(
    "QueryPilot",
    instructions=(
        "QueryPilot answers questions about the Olist e-commerce dataset (Brazilian "
        "marketplace orders, 2016 to 2018; amounts in Brazilian reais). For business "
        "questions, use `ask`: it applies the company's metric definitions (customer, "
        "revenue, late delivery) that raw SQL would miss. Use `list_tables`, "
        f"`describe_table`, and `run_query` (read-only {WAREHOUSE_NAME} SQL) to explore "
        "or to check a specific number. Everything is read-only."
    ),
)
_lock = threading.Lock()  # one tool call at a time: a shared connection and a local model


@lru_cache(maxsize=1)
def _warehouse() -> Warehouse:
    # Opened on first use, so the server starts instantly (Snowflake takes ~10s).
    return get_warehouse()


@lru_cache(maxsize=1)
def _llm() -> LLM:
    return get_llm()


@lru_cache(maxsize=1)
def _agent():
    return build_graph(_llm(), _warehouse())


READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


@server.tool(annotations=READ_ONLY)
def list_tables() -> list[dict]:
    """List the tables in the Olist warehouse, each with a one-line business description."""
    with _lock:
        wh = _warehouse()
        sem = semantic.load_semantic(wh.dataset) or {}
        return [{"table": t, "description": semantic.table_description(sem, t)} for t in wh.list_tables()]


@server.tool(annotations=READ_ONLY)
def describe_table(table: str) -> dict:
    """Describe one table: columns with types and business notes, plus 3 sample rows.

    Args:
        table: a table name from list_tables, e.g. "orders".
    """
    with _lock:
        wh = _warehouse()
        if table not in wh.list_tables():
            raise ValueError(f"Unknown table '{table}'. Call list_tables for valid names.")
        info = wh.describe_table(table)
        sem = semantic.load_semantic(wh.dataset) or {}
        notes = sem.get("tables", {}).get(table, {}).get("columns", {}) or {}
        columns = []
        for name, typ in info.columns:
            entry = notes.get(name)
            note = entry.get("note", "") if isinstance(entry, dict) else (entry or "")
            columns.append({"name": name, "type": typ, "note": note})
        return {
            "table": table,
            "description": semantic.table_description(sem, table),
            "columns": columns,
            "sample_rows": _rows(info.sample.columns, info.sample.rows),
        }


@server.tool(annotations=READ_ONLY)
def run_query(sql: str) -> dict:
    """Run one read-only SQL SELECT and return its rows.

    Guardrails: only a single SELECT on known tables is allowed (no INSERT,
    UPDATE, DELETE, DROP, or multiple statements), LIMIT 1000 is added if
    missing, and the query is cancelled after 30 seconds. At most 100 rows
    are returned; row_count gives the full count.

    For business metrics (revenue, customers, late deliveries) prefer `ask`,
    which applies the company's definitions. Raw SQL can easily get them
    wrong, e.g. revenue is SUM(order_items.price) and excludes freight, and a
    customer is customers.customer_unique_id, not customer_id.

    Args:
        sql: one SELECT statement in the warehouse's SQL dialect.
    """
    with _lock:
        wh = _warehouse()
        checked = validate_sql(sql, set(wh.list_tables()), dialect=wh.dialect)
        if not checked.ok:
            raise ValueError(f"Query rejected by the SQL guardrail: {checked.error}")
        try:
            result = wh.run_query(checked.sql)
        except QueryTimeoutError as e:
            raise ValueError(str(e)) from e
        return {
            "sql": checked.sql,  # what actually ran (LIMIT may have been added)
            "columns": result.columns,
            "rows": _rows(result.columns, result.rows)[:MAX_ROWS_RETURNED],
            "row_count": len(result.rows),
            "truncated": len(result.rows) > MAX_ROWS_RETURNED,
        }


@server.tool(annotations=READ_ONLY)
def ask(question: str) -> dict:
    """Answer a business question about the Olist data, in plain English.

    Runs the full QueryPilot agent: it writes SQL using the company's metric
    definitions, checks it against the guardrails, runs it read-only, repairs
    its own errors, and summarizes the result. Returns the answer, the exact
    SQL that ran, the rows (at most 100), and a suggested chart type. Takes a
    few seconds with Claude or 10 to 30 seconds with the local model.

    Args:
        question: e.g. "Which 5 customer states generated the most revenue?"
    """
    with _lock:
        state = _agent().invoke(
            {"question": question},
            config={"run_name": "mcp ask", "tags": ["mcp"]},  # labels the LangSmith trace
        )
        failed = bool(state.get("error"))
        rows = [] if failed else state.get("rows", [])
        return {
            "answer": state.get("answer", ""),
            "sql": state.get("sql", ""),
            "succeeded": not failed,
            "columns": [] if failed else state.get("columns", []),
            "rows": _rows(state.get("columns", []), rows)[:MAX_ROWS_RETURNED],
            "row_count": len(rows),
            "chart": None if failed else (state.get("chart") or {}).get("type"),
            "repairs": state.get("attempts", 0),
        }


def _rows(columns: list[str], rows: list[tuple]) -> list[dict]:
    """Rows as JSON-safe {column: value} objects, easy for a model to read."""
    return [
        {c: (v if v is None or isinstance(v, (bool, int, float, str)) else json_value(v)) for c, v in zip(columns, r)}
        for r in rows
    ]


def _warm_up_in_background() -> None:
    """Load a local model and its schema prompt before the first `ask`.

    Without this the first `ask` took ~96s with the local model, long enough
    for an MCP client to give up on the call. Holds the lock, so a tool call
    made meanwhile waits for it. Claude needs no warm-up (it would only cost).
    """
    def warm() -> None:
        with _lock:
            try:
                warm_up(_llm(), _warehouse())
            except Exception as e:  # e.g. Ollama not running; `ask` will report it
                logging.getLogger(__name__).warning("warm-up failed: %s", e)

    if needs_warm_up(_llm()):
        threading.Thread(target=warm, daemon=True).start()


def main() -> None:
    # The Ollama client logs every request at INFO; keep the client's log readable.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    _warm_up_in_background()
    server.run("stdio")


if __name__ == "__main__":
    main()
