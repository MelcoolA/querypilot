# Baseline results (do not overwrite)

Frozen results from before any Phase 2 fix to the agent. Result files here are
never replaced or edited; new ones may only be added and listed below.

- `showcase_run_2026-10-02_ollama-qwen2.5-coder-7b.txt`: raw CLI output of the
  8 showcase questions on Olist, run by hand on 2026-10-02 with
  `LLM_PROVIDER=ollama`, `qwen2.5-coder:7b`, before the eval runner existed.
  Summarized in `evals/showcase.md`.
- `2026-10-02_145705_ollama-qwen2.5-coder-7b/`: full 40-question eval
  (`python -m evals.run_evals --baseline`), same model, no Phase 2 fixes.
  Score: 14/40 (35%). Summary in `summary.md`, per-question SQL and answers
  in `results.json`.
