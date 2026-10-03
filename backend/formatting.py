"""Turn query results into text and JSON (CLI, API, MCP server, prompts)."""
from datetime import date, datetime
from decimal import Decimal


def format_table(columns: list[str], rows: list[tuple], max_rows: int = 20) -> str:
    if not columns:
        return "(no columns)"
    shown = [[_cell(v) for v in row] for row in rows[:max_rows]]
    widths = [max([len(c)] + [len(r[i]) for r in shown]) for i, c in enumerate(columns)]
    lines = [
        " | ".join(c.ljust(w) for c, w in zip(columns, widths)),
        "-+-".join("-" * w for w in widths),
    ]
    lines += [" | ".join(v.ljust(w) for v, w in zip(r, widths)) for r in shown]
    if not rows:
        lines.append("(no rows)")
    elif len(rows) > max_rows:
        lines.append(f"... {len(rows) - max_rows} more rows")
    return "\n".join(lines)


def describe_step(node: str, changes: dict) -> str:
    """One short line about what a graph step just did (CLI and API progress)."""
    if changes.get("error"):
        return f"error: {changes['error'].splitlines()[0][:100]}"
    if node == "get_schema":
        return f"{len(changes['tables'])} tables"
    if node == "execute":
        n = len(changes["rows"])
        return f"{n} row{'' if n == 1 else 's'}"
    if node == "repair_sql":
        return f"attempt {changes['attempts']}"
    if node == "pick_chart":
        return changes["chart"]["type"].replace("_", " ")
    return "ok"


def _cell(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def json_value(value):
    """Make a database value JSON-safe: Decimal to float, dates to ISO strings."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
