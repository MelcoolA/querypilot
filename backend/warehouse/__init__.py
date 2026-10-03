"""Pick the warehouse backend from .env (WAREHOUSE=duckdb|snowflake, DATASET=tpch|olist)."""
import os

from dotenv import load_dotenv

from backend.warehouse.base import QUERY_TIMEOUT_S, QueryResult, QueryTimeoutError, TableInfo, Warehouse

load_dotenv()

# Each local dataset is its own DuckDB file, built by its setup script.
DATASET_PATHS = {
    "tpch": "data/tpch.duckdb",    # make data
    "olist": "data/olist.duckdb",  # make data-olist
}


def get_warehouse() -> Warehouse:
    backend = os.getenv("WAREHOUSE", "duckdb").lower()
    if backend == "duckdb":
        from backend.warehouse.duckdb_wh import DuckDBWarehouse

        dataset = os.getenv("DATASET", "tpch").lower()
        if dataset not in DATASET_PATHS:
            raise ValueError(f"Unknown DATASET: {dataset!r} (expected one of {', '.join(DATASET_PATHS)})")
        return DuckDBWarehouse(DATASET_PATHS[dataset], dataset=dataset)
    if backend == "snowflake":
        from backend.warehouse.snowflake_wh import SnowflakeWarehouse

        # Only Olist is loaded into Snowflake (see make data-snowflake).
        return SnowflakeWarehouse(dataset="olist")
    raise ValueError(f"Unknown WAREHOUSE: {backend!r} (expected 'duckdb' or 'snowflake')")


__all__ = [
    "DATASET_PATHS", "QUERY_TIMEOUT_S", "QueryResult", "QueryTimeoutError", "TableInfo", "Warehouse", "get_warehouse",
]
