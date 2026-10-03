"""Each function is one step (node) in the agent graph.

A node receives the current state and returns only the fields it changed.
LangGraph merges those changes into the state for the next node.
"""
import re
from functools import lru_cache

import sqlglot
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers

from backend.agent import charts, prompts, semantic
from backend.agent.state import AgentState
from backend.formatting import format_table
from backend.guardrails.sql_validator import DEFAULT_LIMIT, validate_sql
from backend.llm import LLM, LLMResponse
from backend.warehouse import Warehouse

SUMMARY_MAX_ROWS = 30  # rows shown to the LLM when summarizing; keeps the prompt small


def get_schema(state: AgentState, warehouse: Warehouse) -> dict:
    tables, context = _schema_context(warehouse)
    return {"tables": tables, "schema_context": context}


# The schema doesn't change while the app runs, so build the context once per
# warehouse and reuse it. On DuckDB that saves little; on Snowflake it saves
# ~20 network round trips (and warehouse credits) on every question.
@lru_cache(maxsize=8)
def _schema_context(warehouse: Warehouse) -> tuple[list[str], str]:
    # All 8 Olist tables fit in the prompt. A warehouse with hundreds of tables
    # would need a table-selection step here instead.
    tables = warehouse.list_tables()
    sem = semantic.load_semantic(warehouse.dataset)  # None if the dataset has no semantic layer
    blocks = [semantic.render_header(sem, warehouse.dialect)] if sem else []
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
    return tables, "\n\n".join(blocks)


def write_sql(state: AgentState, llm: LLM, warehouse: Warehouse) -> dict:
    response = llm.complete(
        system=prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompt=prompts.WRITE_SQL_USER.format(
            schema=state["schema_context"],
            examples=semantic.render_examples(semantic.load_semantic(warehouse.dataset), warehouse.dialect),
            question=state["question"],
        ),
    )
    return {
        "sql": extract_sql(response.text), "attempts": 0, "error": "",
        "history": [], "repeated": False, **_tokens(state, response),
    }


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


def pick_chart(state: AgentState) -> dict:
    # Rule-based on the result's shape (see charts.py); no LLM call.
    return {"chart": charts.pick_chart(state["columns"], state["rows"])}


def repair_sql(state: AgentState, llm: LLM, warehouse: Warehouse) -> dict:
    # Show the model every failed attempt, not just the last one, so it can see
    # what it already tried instead of rediscovering the same mistake.
    history = state.get("history", []) + [{"sql": state["sql"], "error": state["error"]}]
    response = llm.complete(
        system=prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompt=prompts.REPAIR_SQL_USER.format(
            schema=state["schema_context"],
            question=state["question"],
            attempts=_format_attempts(history),
        ),
    )
    new_sql = extract_sql(response.text)
    attempts = state["attempts"] + 1
    update = {"sql": new_sql, "attempts": attempts, "history": history, **_tokens(state, response)}

    # Stop early if the model repeats an earlier attempt. At temperature 0 the
    # same SQL fails the same way, so further repairs would only waste time.
    tried = {_canonical_sql(h["sql"], state["tables"], warehouse.dialect) for h in history}
    if _canonical_sql(new_sql, state["tables"], warehouse.dialect) in tried:
        update["repeated"] = True
        update["error"] = f"{state['error']} (stopped early: repair attempt {attempts} repeated an earlier query)"
    return update


def _format_attempts(history: list[dict]) -> str:
    return "\n\n".join(
        f"Attempt {i}:\n```sql\n{h['sql']}\n```\nError: {h['error']}" for i, h in enumerate(history, 1)
    )


def _canonical_sql(sql: str, tables: list[str], dialect: str) -> str:
    """Normalize SQL so cosmetic differences (spacing, case, added LIMIT) don't hide a repeat."""
    result = validate_sql(sql, set(tables), dialect=dialect)
    if not result.ok:  # unparseable: fall back to comparing the text loosely
        return " ".join(sql.lower().split())
    # Lowercase unquoted table/column names only; string literals like 'SP' keep their case.
    tree = normalize_identifiers(sqlglot.parse_one(result.sql, read=dialect), dialect=dialect)
    return tree.sql(dialect=dialect)


def summarize(state: AgentState, llm: LLM) -> dict:
    # Reached either with results, or after the repair budget ran out.
    # Guardrail: when we have no valid result we say so instead of guessing.
    if state.get("error"):
        if _is_blocked_write(state["error"]):
            # A deliberate refusal, not a failure: say so plainly.
            return {
                "answer": (
                    "QueryPilot only reads data. It cannot change or delete anything, so this request "
                    "was blocked by the SQL guardrail. Try asking a question about the data instead."
                )
            }
        n = state["attempts"]
        return {
            "answer": (
                f"I could not answer this confidently. After {n} repair "
                f"attempt{'' if n == 1 else 's'} the query still failed with: {state['error']}"
            )
        }
    rows = state["rows"]
    truncated = len(rows) > SUMMARY_MAX_ROWS
    hit_limit = len(rows) >= DEFAULT_LIMIT  # the guardrail cut the result off
    response = llm.complete(
        system=prompts.SUMMARIZE_SYSTEM,
        prompt=prompts.SUMMARIZE_USER.format(
            question=state["question"],
            sql=state["sql"],
            row_count=len(rows),
            truncated_note=f", first {SUMMARY_MAX_ROWS} shown" if truncated else "",
            result=format_table(state["columns"], rows, max_rows=SUMMARY_MAX_ROWS),
            limit_warning=(
                f"\n\nWARNING: the result hit the {DEFAULT_LIMIT}-row limit, so it is cut off "
                "and is not the full data." if hit_limit else ""
            ),
        ),
    )
    answer = response.text.strip()
    if hit_limit:
        # Added in code, not left to the LLM: the user must always learn the
        # result is partial, even if the model ignores the warning above.
        answer += (
            f"\n\nNote: this result was cut off at {DEFAULT_LIMIT:,} rows, so it does not "
            "cover all the data. Ask a more specific or aggregated question for a complete answer."
        )
    return {"answer": answer, **_tokens(state, response)}


def _is_blocked_write(error: str) -> bool:
    """True when the validator rejected SQL that would change data (DELETE, DROP, ...)."""
    return "Only SELECT queries are allowed" in error or "Forbidden operation" in error


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
