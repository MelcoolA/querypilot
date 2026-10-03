"""Choose how to display a query result: single number, bar, line, or table.

Plain rules on the result's shape, not an LLM call: free, instant, testable,
and easy to explain. The chart spec is what the web UI draws with Recharts.
"""
from datetime import date, datetime
from decimal import Decimal

MAX_BAR_CATEGORIES = 30  # more bars than this is unreadable; show a table instead
MAX_SERIES = 3           # at most 3 numeric columns plotted together
TIME_WORDS = ("year", "quarter", "month", "week", "day", "date")


def pick_chart(columns: list[str], rows: list[tuple]) -> dict:
    """Return a chart spec: {"type": ..., "x": column or None, "y": [columns]}."""
    if not rows or not columns:
        return _table("no rows")

    numeric = [c for i, c in enumerate(columns) if _all(rows, i, _is_number)]

    # One row with one number: show it big ("625 orders were canceled").
    if len(rows) == 1:
        if len(numeric) == 1:
            label = next((c for c in columns if c not in numeric), None)
            return {"type": "single_number", "x": label, "y": numeric, "reason": "one row, one number"}
        return _table("one row with several values")

    # Several rows: need one label column for the x axis and some numbers to plot.
    x = _pick_x(columns, rows, numeric)
    y = [c for c in numeric if c != x][:MAX_SERIES]
    if x is None or not y:
        return _table("no label column plus numbers")

    x_index = columns.index(x)
    if _all(rows, x_index, _is_date) or (x in numeric and any(w in x.lower() for w in TIME_WORDS)):
        return {"type": "line", "x": x, "y": y, "reason": "values over time"}
    if len(rows) <= MAX_BAR_CATEGORIES:
        return {"type": "bar", "x": x, "y": y, "reason": "values per category"}
    return _table(f"more than {MAX_BAR_CATEGORIES} categories")


def _pick_x(columns: list[str], rows: list[tuple], numeric: list[str]) -> str | None:
    """The label column: a date column first, else a text/boolean column,
    else a numeric column whose name says it is time (e.g. "year")."""
    for i, c in enumerate(columns):
        if _all(rows, i, _is_date):
            return c
    for c in columns:
        if c not in numeric:
            return c
    return next((c for c in columns if any(w in c.lower() for w in TIME_WORDS)), None)


def _is_number(value) -> bool:
    # bool is a subclass of int in Python, but True/False are labels, not amounts.
    return value is None or (isinstance(value, (int, float, Decimal)) and not isinstance(value, bool))


def _is_date(value) -> bool:
    return isinstance(value, (date, datetime))


def _all(rows: list[tuple], index: int, check) -> bool:
    values = [r[index] for r in rows]
    return any(v is not None for v in values) and all(check(v) for v in values if v is not None)


def _table(reason: str) -> dict:
    return {"type": "table", "x": None, "y": [], "reason": reason}
