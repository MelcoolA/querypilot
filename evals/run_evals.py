"""Run the agent on every gold question and score it.

    python -m evals.run_evals                  # all 40 questions (make eval)
    python -m evals.run_evals --ids e01,m03    # a subset, for quick checks
    python -m evals.run_evals --baseline       # save into evals/results/baseline/

The LLM comes from .env (LLM_PROVIDER, model name). The dataset comes from
gold.yaml, not from .env, so the gold SQL always runs on the data it was written for.
"""
import argparse
import json
import stat
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from backend.agent import nodes, prompts
from backend.agent.graph import build_graph
from backend.llm import get_llm
from backend.warehouse import DATASET_PATHS
from backend.warehouse.duckdb_wh import DuckDBWarehouse
from evals.scorer import results_match

EVALS_DIR = Path(__file__).parent
RESULTS_DIR = EVALS_DIR / "results"
BASELINE_DIR = RESULTS_DIR / "baseline"
DIFFICULTIES = ["easy", "medium", "hard"]

# USD per million tokens (input, output). Local models cost nothing to call.
# Add an entry before running a paid model; unknown models report cost as n/a.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ids", help="comma-separated question ids to run (default: all)")
    parser.add_argument("--baseline", action="store_true", help="save results under evals/results/baseline/")
    parser.add_argument("--label", default="", help="short name added to the results folder")
    args = parser.parse_args()

    gold = yaml.safe_load((EVALS_DIR / "gold.yaml").read_text())
    questions = gold["questions"]
    if args.ids:
        wanted = set(args.ids.split(","))
        questions = [q for q in questions if q["id"] in wanted]
        if missing := wanted - {q["id"] for q in questions}:
            raise SystemExit(f"Unknown ids: {', '.join(sorted(missing))}")

    llm = get_llm()
    out_dir = _results_dir(args.baseline, llm.name, args.label)  # fail early, before a long run
    warehouse = DuckDBWarehouse(DATASET_PATHS[gold["dataset"]], dataset=gold["dataset"])
    agent = build_graph(llm, warehouse)

    print(f"Running {len(questions)} questions | model {llm.name} | dataset {gold['dataset']}")
    warm_up(llm, warehouse)

    results = []
    for i, q in enumerate(questions, 1):
        record = run_one(q, agent, warehouse, llm.name)
        results.append(record)
        mark = {"correct": "PASS", "wrong": "FAIL", "error": "ERR "}[record["status"]]
        print(f"[{i:>2}/{len(questions)}] {mark} {q['id']} {record['latency_s']:6.1f}s "
              f"{record['repairs']}r  {q['question'][:60]}"
              + ("" if record["status"] == "correct" else f"  ({record['reason'][:70]})"), flush=True)

    summary = build_summary(results, llm.name, gold["dataset"])
    print("\n" + summary)
    save(out_dir, results, summary, llm.name, protect=args.baseline)
    print(f"Saved to {out_dir}")


def warm_up(llm, warehouse) -> None:
    """Send one untimed request with the real schema prompt before scoring starts.

    Local models load into memory on first use, and Ollama caches the processed
    prompt prefix (the ~3k-token schema shared by every question). Without this,
    the first question alone pays both costs and skews average latency.
    """
    schema = nodes.get_schema({}, warehouse)["schema_context"]
    llm.complete(
        prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompts.WRITE_SQL_USER.format(schema=schema, question="How many rows are in the orders table?"),
    )


def run_one(q: dict, agent, warehouse, model: str) -> dict:
    record = {
        "id": q["id"], "difficulty": q["difficulty"], "traps": q.get("traps", []),
        "question": q["question"], "status": "error", "reason": "", "sql": "", "answer": "",
        "latency_s": 0.0, "repairs": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": None,
    }
    start = time.time()
    try:
        state = agent.invoke({"question": q["question"]})
    except Exception as e:  # a crash counts as a wrong answer, not a crashed eval
        record["latency_s"] = round(time.time() - start, 2)
        record["reason"] = f"agent crashed: {type(e).__name__}: {e}"
        return record
    record.update(
        latency_s=round(time.time() - start, 2),
        sql=state.get("sql", ""),
        answer=state.get("answer", ""),
        repairs=state.get("attempts", 0),
        input_tokens=state.get("input_tokens", 0),
        output_tokens=state.get("output_tokens", 0),
    )
    record["cost_usd"] = cost(model, record["input_tokens"], record["output_tokens"])

    if state.get("error"):
        record["reason"] = f"agent gave up: {state['error'].splitlines()[0]}"
        return record
    gold_rows = warehouse.run_query(q["sql"]).rows
    match, reason = results_match(gold_rows, state.get("rows", []))
    record["status"] = "correct" if match else "wrong"
    record["reason"] = reason
    return record


def cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model.startswith("ollama:"):
        return 0.0
    if model not in PRICES_PER_MTOK:
        return None
    price_in, price_out = PRICES_PER_MTOK[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def build_summary(results: list[dict], model: str, dataset: str) -> str:
    def acc(rows):
        n = len(rows)
        correct = sum(r["status"] == "correct" for r in rows)
        return f"{correct}/{n} ({100 * correct / n:.0f}%)" if n else "-"

    def avg(key, rows):
        return sum(r[key] for r in rows) / len(rows) if rows else 0.0

    by_diff = {d: [r for r in results if r["difficulty"] == d] for d in DIFFICULTIES}
    by_trap = defaultdict(list)
    for r in results:
        for t in r["traps"]:
            by_trap[t].append(r)
    costs = [r["cost_usd"] for r in results]
    cost_text = "n/a (no price set)" if None in costs else f"${sum(costs) / len(costs):.4f}"

    lines = [
        f"## Eval summary: {model} on {dataset}, {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Accuracy (overall) | {acc(results)} |",
        *[f"| Accuracy ({d}) | {acc(rows)} |" for d, rows in by_diff.items()],
        f"| Agent gave up / crashed | {sum(r['status'] == 'error' for r in results)} |",
        f"| Avg latency | {avg('latency_s', results):.1f}s |",
        f"| Avg tokens (in / out) | {avg('input_tokens', results):.0f} / {avg('output_tokens', results):.0f} |",
        f"| Avg cost per question | {cost_text} |",
        f"| Repairs (total / avg) | {sum(r['repairs'] for r in results)} / {avg('repairs', results):.2f} |",
        f"| Questions needing a repair | {sum(r['repairs'] > 0 for r in results)} |",
        "",
        "| Trap | Accuracy |",
        "|---|---|",
        *[f"| {t} | {acc(rows)} |" for t, rows in sorted(by_trap.items())],
        "",
        "| Id | Result | Repairs | Latency | Reason |",
        "|---|---|---|---|---|",
        *[f"| {r['id']} | {r['status']} | {r['repairs']} | {r['latency_s']:.1f}s | "
          f"{r['reason'].replace('|', '/')[:90]} |" for r in results],
    ]
    return "\n".join(lines)


def _results_dir(baseline: bool, model: str, label: str) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_model = model.replace(":", "-").replace("/", "-")  # e.g. ollama-qwen2.5-coder-7b
    name = "_".join(p for p in [stamp, safe_model, label] if p)
    out = (BASELINE_DIR if baseline else RESULTS_DIR) / name
    if out.exists():  # the baseline folder must never be overwritten
        raise SystemExit(f"{out} already exists; refusing to overwrite.")
    return out


def save(out_dir: Path, results: list[dict], summary: str, model: str, protect: bool) -> None:
    out_dir.mkdir(parents=True)
    (out_dir / "results.json").write_text(json.dumps({"model": model, "results": results}, indent=2, default=str))
    (out_dir / "summary.md").write_text(summary + "\n")
    if protect:  # baseline files are made read-only so they can't be edited by accident
        for f in out_dir.iterdir():
            f.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


if __name__ == "__main__":
    main()
