"""Decide whether the agent's result set matches the gold result set.

Rules (kept lenient on format, strict on numbers):
- Row order is ignored, but the row count must match.
- Column names are ignored; agent columns are matched to gold columns by value.
  Extra agent columns are fine, but every gold column must be present.
- Numbers are rounded to 2 decimals; dates and timestamps become 'YYYY-MM-DD';
  month strings like '2017-11' become '2017-11-01'.
- A column of January 1st dates also matches plain years (2017-01-01 vs 2017),
  since DATE_TRUNC('year', ...) and YEAR(...) are both valid ways to answer.
- Boolean gold columns (e.g. is_late) are not compared, because the agent may
  label groups as 'late' / 'on time' instead. The numeric columns next to
  them must still match, so the groups' values are still checked.
"""
import re
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from itertools import permutations

FLOAT_DECIMALS = 2
MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def normalize(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return round(float(value), FLOAT_DECIMALS) + 0.0  # + 0.0 turns -0.0 into 0.0
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        month = MONTH_RE.match(text)
        if month:
            return f"{month.group(1)}-{month.group(2)}-01"
        # '2017-11-01 00:00:00' and '2017-11-01' should compare equal
        if re.match(r"^\d{4}-\d{2}-\d{2}[ T]00:00:00$", text):
            return text[:10]
        return text
    return value


def _add_year_columns(rows: list[tuple]) -> list[tuple]:
    """For each column holding only Jan 1st dates, append a copy as plain years.

    Appending (instead of replacing) keeps the date form available too, so a
    month column that happens to be '2017-01-01' still matches a date gold column.
    """
    extra = []
    for j in range(len(rows[0])):
        values = [r[j] for r in rows]
        if all(isinstance(v, str) and re.match(r"^\d{4}-01-01$", v) for v in values):
            extra.append(j)
    return [r + tuple(float(r[j][:4]) for j in extra) for r in rows]


def results_match(gold_rows: list[tuple], agent_rows: list[tuple]) -> tuple[bool, str]:
    """Return (match, reason). The reason explains a mismatch in one line."""
    if len(gold_rows) != len(agent_rows):
        return False, f"row count {len(agent_rows)}, expected {len(gold_rows)}"
    if not gold_rows:
        return True, "both empty"

    gold = [tuple(normalize(v) for v in row) for row in gold_rows]
    agent = [tuple(normalize(v) for v in row) for row in agent_rows]

    # Drop boolean label columns from the gold side (see module docstring).
    keep = [j for j in range(len(gold[0])) if not all(isinstance(r[j], bool) or r[j] is None for r in gold)]
    gold = [tuple(r[j] for j in keep) for r in gold]
    agent = _add_year_columns(agent)
    n_gold, n_agent = len(keep), len(agent[0])
    if n_gold == 0:
        return True, "only label columns"
    if n_agent < n_gold:
        return False, f"{n_agent} columns, expected at least {n_gold}"

    # Cheap filter first: an agent column can only stand in for a gold column
    # if both hold the same multiset of values.
    def col(rows, j):
        return Counter(r[j] for r in rows)

    candidates = [
        [k for k in range(n_agent) if col(agent, k) == col(gold, j)] for j in range(n_gold)
    ]
    for j, cands in enumerate(candidates):
        if not cands:
            return False, f"no agent column matches gold column {j + 1} (values differ)"

    # Then check whole rows, trying each consistent column assignment.
    gold_counter = Counter(gold)
    for assignment in permutations(range(n_agent), n_gold):
        if all(assignment[j] in candidates[j] for j in range(n_gold)):
            projected = Counter(tuple(r[k] for k in assignment) for r in agent)
            if projected == gold_counter:
                return True, "match"
    return False, "columns match individually but rows pair up differently"
