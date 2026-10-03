"""Exact facts about a result, computed in code for the summarize prompt.

A small model reading a 12-row table can misread it (it once wrote "8,000
orders in January" when the table said 800). Stating the lowest and highest
values outright, with the row they belong to, gives it numbers to copy
instead of numbers to find.
"""
from datetime import date, datetime
from decimal import Decimal

MAX_FACT_COLUMNS = 3  # same cap as charted series; keeps the prompt short


def result_facts(columns: list[str], rows: list[tuple]) -> list[str]:
    """Lines like "lowest orders: 800 (month 2017-01-01)". Empty for 0 or 1 rows."""
    if len(rows) < 2:
        return []
    numeric = [i for i in range(len(columns)) if _all_numbers(rows, i)]
    label = next((i for i in range(len(columns)) if i not in numeric), None)

    facts = [f"rows: {len(rows)}"]
    for i in numeric[:MAX_FACT_COLUMNS]:
        present = [r for r in rows if r[i] is not None]
        if not present:
            continue
        low = min(present, key=lambda r: r[i])
        high = max(present, key=lambda r: r[i])
        facts.append(f"lowest {columns[i]}: {_number(low[i])}{_where(columns, label, low)}")
        facts.append(f"highest {columns[i]}: {_number(high[i])}{_where(columns, label, high)}")
    return facts if len(facts) > 1 else []


def _where(columns: list[str], label: int | None, row: tuple) -> str:
    return "" if label is None else f" ({columns[label]} {_label(row[label])})"


def _label(value) -> str:
    # Show midnight timestamps as plain dates (DATE_TRUNC('month') results).
    if isinstance(value, datetime) and value.time() == datetime.min.time():
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):  # a plain date has no time part to separate
        return value.isoformat()
    return str(value)


def _number(value) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return f"{float(value):,.2f}"


def _all_numbers(rows: list[tuple], i: int) -> bool:
    values = [r[i] for r in rows if r[i] is not None]
    # bool is an int in Python, but True/False are labels, not amounts.
    return bool(values) and all(
        isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) for v in values
    )
