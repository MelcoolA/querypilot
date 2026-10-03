"""One warehouse interface, multiple backends (DuckDB now, Snowflake in Phase 4)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


QUERY_TIMEOUT_S = 30  # guardrail 5: no single query may run longer than this


class QueryTimeoutError(Exception):
    """Raised when a query is cancelled for running longer than the timeout."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple]


@dataclass
class TableInfo:
    name: str
    columns: list[tuple[str, str]]  # (column name, type)
    sample: QueryResult = field(default_factory=lambda: QueryResult([], []))


class Warehouse(ABC):
    dialect: str  # sqlglot dialect name, e.g. "duckdb" or "snowflake"
    dataset: str = ""  # e.g. "olist"; picks the semantic layer file, if one exists

    @abstractmethod
    def list_tables(self) -> list[str]: ...

    @abstractmethod
    def describe_table(self, table: str) -> TableInfo: ...

    @abstractmethod
    def run_query(self, sql: str) -> QueryResult: ...
