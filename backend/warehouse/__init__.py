"""Pick the warehouse backend from .env (WAREHOUSE=duckdb|snowflake)."""
import os

from dotenv import load_dotenv

from backend.warehouse.base import QueryResult, TableInfo, Warehouse

load_dotenv()


def get_warehouse() -> Warehouse:
    backend = os.getenv("WAREHOUSE", "duckdb").lower()
    if backend == "duckdb":
        from backend.warehouse.duckdb_wh import DuckDBWarehouse

        return DuckDBWarehouse(os.getenv("DUCKDB_PATH", "data/tpch.duckdb"))
    if backend == "snowflake":
        raise NotImplementedError("Snowflake backend arrives in Phase 4.")
    raise ValueError(f"Unknown WAREHOUSE: {backend!r} (expected 'duckdb' or 'snowflake')")


__all__ = ["QueryResult", "TableInfo", "Warehouse", "get_warehouse"]
