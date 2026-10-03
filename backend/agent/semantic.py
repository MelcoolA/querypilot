"""Load the semantic layer (semantic/<dataset>.yaml) and render it as prompt text.

The semantic layer adds business meaning the raw schema can't express:
definitions ("revenue = SUM(price)"), join paths, and per-column notes.
"""
from functools import lru_cache
from pathlib import Path

import yaml

from backend.warehouse import Warehouse

SEMANTIC_DIR = Path(__file__).resolve().parents[2] / "semantic"
MAX_LISTED_VALUES = 100  # cap for list_values columns, keeps the prompt bounded


@lru_cache(maxsize=None)
def load_semantic(dataset: str) -> dict | None:
    path = SEMANTIC_DIR / f"{dataset}.yaml"
    if not dataset or not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def render_header(sem: dict) -> str:
    """Definitions, joins, and column locations: goes above the table list."""
    lines = ["BUSINESS DEFINITIONS (follow these exactly):"]
    lines += [f"- {term}: {' '.join(text.split())}" for term, text in sem.get("definitions", {}).items()]
    if joins := sem.get("joins"):
        lines += ["", "JOIN PATHS:"] + [f"- {j}" for j in joins]
    if locations := sem.get("column_locations"):
        lines += ["", f"COLUMN LOCATIONS: {' '.join(locations.split())}"]
    return "\n".join(lines)


def render_columns(sem: dict, table: str, columns: list[tuple[str, str]], warehouse: Warehouse) -> str:
    """One line per column, with its note and (if flagged) its distinct values."""
    notes = sem.get("tables", {}).get(table, {}).get("columns", {}) or {}
    lines = []
    for name, typ in columns:
        entry = notes.get(name)
        # A column entry is either a plain note string or {note, list_values}.
        note = entry.get("note", "") if isinstance(entry, dict) else (entry or "")
        line = f"  {name} {typ}" + (f": {note}" if note else "")
        if isinstance(entry, dict) and entry.get("list_values"):
            line += f" Values: {_distinct_values(warehouse, table, name)}"
        lines.append(line)
    return "\n".join(lines)


def render_examples(sem: dict | None) -> str:
    """Worked question -> SQL examples for the write_sql prompt ("" if none)."""
    examples = (sem or {}).get("examples") or []
    if not examples:
        return ""
    parts = [f"Question: {e['question']}\n```sql\n{e['sql'].strip()}\n```" for e in examples]
    return "EXAMPLES of correct queries on this data:\n\n" + "\n\n".join(parts) + "\n\n"


def table_description(sem: dict, table: str) -> str:
    return sem.get("tables", {}).get(table, {}).get("description", "")


def _distinct_values(warehouse: Warehouse, table: str, column: str) -> str:
    # Read from the data, not hand-typed, so the list can't drift from reality.
    # Table and column names come from the warehouse's own schema, not user input.
    result = warehouse.run_query(
        f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL '
        f'ORDER BY 1 LIMIT {MAX_LISTED_VALUES + 1}'
    )
    values = [repr(r[0]) for r in result.rows[:MAX_LISTED_VALUES]]
    more = ", ..." if len(result.rows) > MAX_LISTED_VALUES else ""
    return ", ".join(values) + more
