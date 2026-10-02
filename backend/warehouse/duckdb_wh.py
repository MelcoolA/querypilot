"""DuckDB backend over a local TPC-H database file."""
from functools import lru_cache
from pathlib import Path

import duckdb

from backend.warehouse.base import QueryResult, TableInfo, Warehouse

SAMPLE_ROWS = 3


class DuckDBWarehouse(Warehouse):
    dialect = "duckdb"

    def __init__(self, path: str, dataset: str = ""):
        self.dataset = dataset
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} not found. Run `make data` to generate TPC-H data.")
        # Guardrail 1: the connection itself is read-only, so even if a write
        # slipped past the SQL validator, DuckDB would refuse it.
        self.conn = duckdb.connect(path, read_only=True)

    def list_tables(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchall()
        return [r[0] for r in rows]

    # Schema context never changes during a session, so cache it.
    @lru_cache(maxsize=None)
    def describe_table(self, table: str) -> TableInfo:
        if table not in self.list_tables():
            raise ValueError(f"Unknown table: {table}")
        cols = self.conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ? ORDER BY ordinal_position",
            [table],
        ).fetchall()
        # Safe to interpolate: `table` was checked against the real table list above.
        sample = self.run_query(f'SELECT * FROM "{table}" LIMIT {SAMPLE_ROWS}')
        return TableInfo(name=table, columns=[(c, t) for c, t in cols], sample=sample)

    def run_query(self, sql: str) -> QueryResult:
        cursor = self.conn.cursor()  # fresh cursor per query keeps results isolated
        cursor.execute(sql)
        columns = [d[0] for d in cursor.description]
        return QueryResult(columns=columns, rows=cursor.fetchall())
