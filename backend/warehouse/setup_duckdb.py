"""Generate the local TPC-H database: python -m backend.warehouse.setup_duckdb"""
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()

SCALE_FACTOR = 0.1  # ~150k orders, ~600k lineitems: realistic shape, still fast on a laptop


def main() -> None:
    path = Path(os.getenv("DUCKDB_PATH", "data/tpch.duckdb"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"{path} already exists, nothing to do. Delete it to regenerate.")
        return
    # This is the only writable connection in the project, used once to build the data.
    conn = duckdb.connect(str(path))
    conn.execute("INSTALL tpch; LOAD tpch;")
    conn.execute(f"CALL dbgen(sf={SCALE_FACTOR})")
    for (table,) in conn.execute("SHOW TABLES").fetchall():
        count = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        print(f"  {table:<10} {count:>9,} rows")
    conn.close()
    print(f"Created {path}")


if __name__ == "__main__":
    main()
