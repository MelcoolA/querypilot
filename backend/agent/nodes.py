"""Each function is one step (node) in the agent graph.

A node receives the current state and returns only the fields it changed.
LangGraph merges those changes into the state for the next node.
"""
import re

from backend.agent import prompts, semantic
from backend.agent.state import AgentState
from backend.formatting import format_table
from backend.guardrails.sql_validator import validate_sql
from backend.llm import LLM, LLMResponse
from backend.warehouse import Warehouse

SUMMARY_MAX_ROWS = 30  # rows shown to the LLM when summarizing; keeps the prompt small


def get_schema(state: AgentState, warehouse: Warehouse) -> dict:
    # TPC-H has only 8 tables, so Phase 1 sends all of them. A real warehouse with
    # hundreds of tables needs a table-selection step here instead.
    tables = warehouse.list_tables()
    sem = semantic.load_semantic(warehouse.dataset)  # None if the dataset has no semantic layer
    blocks = [semantic.render_header(sem)] if sem else []
    for name in tables:
        info = warehouse.describe_table(name)
        sample = format_table(info.sample.columns, info.sample.rows)
        if sem:
            description = semantic.table_description(sem, name)
            columns = semantic.render_columns(sem, name, info.columns, warehouse)
            header = f"TABLE {name}" + (f": {description}" if description else "")
            blocks.append(f"{header}\nColumns:\n{columns}\nSample rows:\n{sample}")
        else:
            cols = ", ".join(f"{c} {t}" for c, t in info.columns)
            blocks.append(f"TABLE {name} ({cols})\nSample rows:\n{sample}")
    return {"tables": tables, "schema_context": "\n\n".join(blocks)}


def write_sql(state: AgentState, llm: LLM, warehouse: Warehouse) -> dict:
    response = llm.complete(
        system=prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompt=prompts.WRITE_SQL_USER.format(schema=state["schema_context"], question=state["question"]),
    )
    return {"sql": extract_sql(response.text), "attempts": 0, "error": "", **_tokens(state, response)}


def validate(state: AgentState, warehouse: Warehouse) -> dict:
    result = validate_sql(state["sql"], set(state["tables"]), dialect=warehouse.dialect)
    if not result.ok:
        return {"error": result.error}
    return {"sql": result.sql, "error": ""}


def execute(state: AgentState, warehouse: Warehouse) -> dict:
    try:
        result = warehouse.run_query(state["sql"])
    except Exception as e:  # any DB error goes back to the LLM as feedback
        return {"error": f"{type(e).__name__}: {e}"}
    return {"columns": result.columns, "rows": result.rows, "error": ""}


def repair_sql(state: AgentState, llm: LLM, warehouse: Warehouse) -> dict:
    response = llm.complete(
        system=prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompt=prompts.REPAIR_SQL_USER.format(
            schema=state["schema_context"],
            question=state["question"],
            sql=state["sql"],
            error=state["error"],
        ),
    )
    return {"sql": extract_sql(response.text), "attempts": state["attempts"] + 1, **_tokens(state, response)}


def summarize(state: AgentState, llm: LLM) -> dict:
    # Reached either with results, or after the repair budget ran out.
    # Guardrail: when we have no valid result we say so instead of guessing.
    if state.get("error"):
        return {
            "answer": (
                f"I could not answer this confidently. After {state['attempts']} repair "
                f"attempts the query still failed with: {state['error']}"
            )
        }
    rows = state["rows"]
    truncated = len(rows) > SUMMARY_MAX_ROWS
    response = llm.complete(
        system=prompts.SUMMARIZE_SYSTEM,
        prompt=prompts.SUMMARIZE_USER.format(
            question=state["question"],
            sql=state["sql"],
            row_count=len(rows),
            truncated_note=f", first {SUMMARY_MAX_ROWS} shown" if truncated else "",
            result=format_table(state["columns"], rows, max_rows=SUMMARY_MAX_ROWS),
        ),
    )
    return {"answer": response.text.strip(), **_tokens(state, response)}


def extract_sql(text: str) -> str:
    """Pull SQL out of an LLM reply. Models often wrap it in ```sql fences."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    sql = match.group(1) if match else text
    return sql.strip().rstrip(";").strip()


def _tokens(state: AgentState, response: LLMResponse) -> dict:
    return {
        "input_tokens": state.get("input_tokens", 0) + response.input_tokens,
        "output_tokens": state.get("output_tokens", 0) + response.output_tokens,
    }
