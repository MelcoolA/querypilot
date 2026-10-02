"""Check LLM-written SQL before it touches the warehouse.

We parse the SQL into a syntax tree with sqlglot instead of using regex, because
regex is easy to fool (comments, string literals, odd casing).
"""
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DEFAULT_LIMIT = 1000

# Node types that can change data or schema. A SELECT should never contain one.
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge,
    exp.Create, exp.Drop, exp.Alter, exp.Command,
)


@dataclass
class ValidationResult:
    ok: bool
    sql: str = ""     # the cleaned SQL to run (with LIMIT added), when ok
    error: str = ""   # why it was rejected, when not ok. Fed back to repair_sql.


def validate_sql(sql: str, allowed_tables: set[str], dialect: str = "duckdb") -> ValidationResult:
    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except ParseError as e:
        return ValidationResult(ok=False, error=f"SQL syntax error: {e}")

    if len(statements) != 1:
        return ValidationResult(ok=False, error=f"Expected exactly one statement, got {len(statements)}.")
    tree = statements[0]

    # exp.Query covers SELECT, UNION / INTERSECT / EXCEPT, and WITH ... SELECT.
    if not isinstance(tree, exp.Query):
        return ValidationResult(ok=False, error=f"Only SELECT queries are allowed, got {tree.key.upper()}.")
    for node in tree.walk():
        if isinstance(node, FORBIDDEN_NODES):
            return ValidationResult(ok=False, error=f"Forbidden operation: {node.key.upper()}.")

    # CTE names (WITH x AS ...) show up as tables in the tree but are not real tables.
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    allowed = {t.lower() for t in allowed_tables}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if not name:
            # e.g. FROM read_csv('/etc/passwd'): table functions can read local files.
            return ValidationResult(ok=False, error=f"Table functions are not allowed: {table.sql()}")
        if name not in allowed and name not in cte_names:
            return ValidationResult(
                ok=False,
                error=f"Unknown table '{table.name}'. Allowed tables: {', '.join(sorted(allowed))}.",
            )

    # Cap result size so a careless query cannot pull millions of rows.
    if tree.args.get("limit") is None:
        tree = tree.limit(DEFAULT_LIMIT)

    return ValidationResult(ok=True, sql=tree.sql(dialect=dialect, pretty=True))
