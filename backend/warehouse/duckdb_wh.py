"""DuckDB backend over a local database file (TPC-H or Olist)."""
import threading
from functools import lru_cache
from pathlib import Path

import duckdb

from backend.warehouse.base import QUERY_TIMEOUT_S, QueryResult, QueryTimeoutError, TableInfo, Warehouse

SAMPLE_ROWS = 3


class DuckDBWarehouse(Warehouse):
    dialect = "duckdb"

    def __init__(self, path: str, dataset: str = "", timeout_s: float = QUERY_TIMEOUT_S):
        self.dataset = dataset
        self.timeout_s = timeout_s
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
        # Guardrail 5: DuckDB has no statement timeout setting, so a timer thread
        # interrupts the query if it runs too long.
        timer = threading.Timer(self.timeout_s, cursor.interrupt)
        timer.start()
        try:
            cursor.execute(sql)
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
        except duckdb.InterruptException as e:
            raise QueryTimeoutError(
                f"Query timed out after {self.timeout_s:g}s. Write a simpler or more selective query."
            ) from e
        finally:
            timer.cancel()
        return QueryResult(columns=columns, rows=rows)
