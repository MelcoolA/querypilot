"""Re-score a saved eval run with the current scorer, without calling the LLM.

    python -m evals.rescore evals/results/<run folder>

Re-runs each saved agent SQL (cheap, read-only) and compares it to the gold SQL.
Prints a fresh summary; writes nothing, so frozen baseline files stay untouched.
Use it whenever the scorer changes, so old and new runs stay comparable.
"""
import json
import sys
from pathlib import Path

import yaml

from backend.agent.semantic import to_dialect
from backend.warehouse import DATASET_PATHS
from backend.warehouse.duckdb_wh import DuckDBWarehouse
from evals.run_evals import EVALS_DIR, build_summary
from evals.scorer import results_match


def main() -> None:
    run_dir = Path(sys.argv[1])
    saved = json.loads((run_dir / "results.json").read_text())
    gold = yaml.safe_load((EVALS_DIR / "gold.yaml").read_text())
    gold_sql = {q["id"]: q["sql"] for q in gold["questions"]}
    # Re-score on the warehouse the run used (older runs predate the field: DuckDB).
    if saved.get("warehouse", "duckdb") == "snowflake":
        from backend.warehouse.snowflake_wh import SnowflakeWarehouse

        warehouse = SnowflakeWarehouse()
    else:
        warehouse = DuckDBWarehouse(DATASET_PATHS[gold["dataset"]])

    changed = []
    for r in saved["results"]:
        if r["status"] == "error":  # the agent gave up; nothing to re-score
            continue
        match, reason = results_match(
            warehouse.run_query(to_dialect(gold_sql[r["id"]], warehouse.dialect)).rows, warehouse.run_query(r["sql"]).rows
        )
        new_status = "correct" if match else "wrong"
        if new_status != r["status"]:
            changed.append(f"{r['id']}: {r['status']} -> {new_status}")
        r["status"], r["reason"] = new_status, reason

    print(f"Re-scored {run_dir.name}")
    print("Changed: " + (", ".join(changed) if changed else "none"))
    print("\n" + build_summary(saved["results"], saved["model"], gold["dataset"]).split("\n| Trap")[0])


if __name__ == "__main__":
    main()
