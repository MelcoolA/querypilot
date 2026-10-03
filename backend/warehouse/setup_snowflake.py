"""Load the Olist tables from the local DuckDB file into Snowflake.

    python -m backend.warehouse.setup_snowflake   (or: make data-snowflake)

Runs as the short-lived loader service user (snowflake/loader_user.sql), not
the agent's read-only user. For each table: export it from DuckDB to Parquet,
upload it to the table's Snowflake stage, COPY it in, and check that the row
count matches DuckDB exactly.
"""
import os
import tempfile
from pathlib import Path

import duckdb

from backend.warehouse import DATASET_PATHS
from backend.warehouse.snowflake_wh import _require, connect

# DuckDB type -> Snowflake type. The Olist database only uses these four.
TYPE_MAP = {"VARCHAR": "VARCHAR", "BIGINT": "NUMBER(38,0)", "DOUBLE": "FLOAT", "TIMESTAMP": "TIMESTAMP_NTZ"}


def main() -> None:
    local = duckdb.connect(DATASET_PATHS["olist"], read_only=True)
    tables = [t for (t,) in local.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1").fetchall()]

    sf = connect(_require("SNOWFLAKE_LOADER_USER"), _require("SNOWFLAKE_LOADER_KEY_FILE"), "QUERYPILOT_LOADER")
    cur = sf.cursor()
    print(f"Loading {len(tables)} tables into {os.getenv('SNOWFLAKE_DATABASE')}.{os.getenv('SNOWFLAKE_SCHEMA')}")

    with tempfile.TemporaryDirectory() as tmp:
        for table in tables:
            columns = local.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'main' AND table_name = ? ORDER BY ordinal_position", [table]).fetchall()
            unknown = {t for _, t in columns if t not in TYPE_MAP}
            if unknown:
                raise ValueError(f"{table}: no Snowflake mapping for types {unknown}")

            # 1. Export from DuckDB. Table names come from DuckDB's own catalog.
            parquet = Path(tmp) / f"{table}.parquet"
            local.execute(f"COPY \"{table}\" TO '{parquet}' (FORMAT PARQUET)")

            # 2. Create the table (replacing any earlier load) with mapped types.
            column_sql = ", ".join(f"{name} {TYPE_MAP[typ]}" for name, typ in columns)
            cur.execute(f"CREATE OR REPLACE TABLE {table} ({column_sql})")

            # 3. Upload to the table's own stage, then COPY in by column name.
            cur.execute(f"PUT 'file://{parquet}' @%{table} AUTO_COMPRESS = FALSE OVERWRITE = TRUE")
            cur.execute(
                f"COPY INTO {table} FROM @%{table} "
                "FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE) "
                "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE PURGE = TRUE"
            )

            # 4. The row count must match exactly, or the load is not trusted.
            expected = local.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            loaded = cur.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            status = "ok" if loaded == expected else "MISMATCH"
            print(f"  {table:<15} {loaded:>9,} rows (DuckDB {expected:,}) {status}")
            if loaded != expected:
                raise SystemExit(f"Row count mismatch for {table}; stopping.")

    sf.close()
    print("Done. Disable the loader now: ALTER USER querypilot_loader_svc SET DISABLED = TRUE;")


if __name__ == "__main__":
    main()
