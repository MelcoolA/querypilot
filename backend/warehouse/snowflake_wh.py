"""Snowflake backend: the same Olist tables, in a cloud warehouse.

The agent signs in as a read-only SERVICE user with an RSA key pair (no
password). Read-only is enforced by Snowflake itself (the role has only
USAGE and SELECT), and Snowflake also enforces the 30s statement timeout.
"""
import os
from functools import lru_cache

import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.errors import ProgrammingError

from backend.warehouse.base import QUERY_TIMEOUT_S, QueryResult, QueryTimeoutError, TableInfo, Warehouse

load_dotenv()

SAMPLE_ROWS = 3
# Snowflake error codes for a statement that was cancelled for running too long.
TIMEOUT_ERRNOS = {604, 630}


class SnowflakeWarehouse(Warehouse):
    dialect = "snowflake"

    def __init__(self, dataset: str = "olist", timeout_s: float = QUERY_TIMEOUT_S):
        self.dataset = dataset
        self.timeout_s = timeout_s
        self.schema = _require("SNOWFLAKE_SCHEMA").upper()
        self.conn = connect(_require("SNOWFLAKE_USER"), _require("SNOWFLAKE_PRIVATE_KEY_FILE"), _require("SNOWFLAKE_ROLE"))

    def list_tables(self) -> list[str]:
        # Snowflake stores unquoted names in UPPERCASE; the agent and the
        # semantic layer use lowercase, which Snowflake matches case-insensitively.
        rows = self._fetch(
            "SELECT LOWER(table_name) FROM information_schema.tables "
            "WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY 1",
            [self.schema],
        )
        return [r[0] for r in rows]

    @lru_cache(maxsize=None)  # schema context never changes during a session
    def describe_table(self, table: str) -> TableInfo:
        if table not in self.list_tables():
            raise ValueError(f"Unknown table: {table}")
        cols = self._fetch(
            "SELECT LOWER(column_name), data_type FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
            [self.schema, table.upper()],
        )
        # Safe to interpolate: `table` was checked against the real table list above.
        sample = self.run_query(f"SELECT * FROM {table} LIMIT {SAMPLE_ROWS}")
        return TableInfo(name=table, columns=[(c, t) for c, t in cols], sample=sample)

    def run_query(self, sql: str) -> QueryResult:
        cursor = self.conn.cursor()
        try:
            # Guardrail 5 twice: the client cancels after timeout_s, and Snowflake
            # itself enforces STATEMENT_TIMEOUT_IN_SECONDS=30 on this user.
            cursor.execute(sql, timeout=self.timeout_s)
        except ProgrammingError as e:
            if e.errno in TIMEOUT_ERRNOS:
                raise QueryTimeoutError(
                    f"Query timed out after {self.timeout_s:g}s. Write a simpler or more selective query."
                ) from e
            raise
        # Lowercase column names so results look the same as on DuckDB.
        columns = [d[0].lower() for d in cursor.description]
        return QueryResult(columns=columns, rows=[tuple(r) for r in cursor.fetchall()])

    def _fetch(self, sql: str, params: list) -> list[tuple]:
        return self.conn.cursor().execute(sql, params).fetchall()


def connect(user: str, key_file: str, role: str):
    """Open a Snowflake connection with key-pair auth, using settings from .env."""
    return snowflake.connector.connect(
        account=_require("SNOWFLAKE_ACCOUNT"),
        user=user,
        private_key_file=key_file,
        role=role,
        warehouse=_require("SNOWFLAKE_WAREHOUSE"),
        database=_require("SNOWFLAKE_DATABASE"),
        schema=_require("SNOWFLAKE_SCHEMA"),
        login_timeout=30,
        client_session_keep_alive=True,  # the API stays connected for hours
    )


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise ValueError(f"{var} is not set. Add it to your .env file.")
    return value
