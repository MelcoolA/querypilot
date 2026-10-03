# Warehouse Analyst Agent

A text-to-SQL analytics agent. A business user asks a question in plain English
("Which regions had the biggest revenue drop last quarter?"). The agent finds the
right tables, writes SQL, validates it, runs it read-only against a data warehouse,
fixes its own errors, charts the result, and explains the answer in plain English.

## Why this project exists

This is a portfolio project for building real depth in applied AI: agents,
evals, guardrails, and data infrastructure. The developer (Melad) must be able
to explain and defend every design choice.
So when you (Claude Code) build something:

- Explain what you built and why in 3 to 5 plain sentences after each step.
- Prefer simple, readable code over clever code.
- Don't add dependencies or features outside this spec without asking.
- Leave short comments on any non-obvious decision.

## Tech stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python 3.11+ | Backend and agent |
| Agent framework | LangGraph (LangChain) | Explicit graph of steps, easy to explain |
| LLM | Ollama (local, free) or Claude via Anthropic API | Switch with `LLM_PROVIDER=ollama|anthropic` in `.env`; model names in `.env`, never hardcoded |
| Dev database | DuckDB with TPC-H data | Local, free, fast to iterate |
| Target database | Snowflake (free trial) | `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` |
| SQL validation | sqlglot | Parse, check read-only, add LIMIT |
| API | FastAPI | `/ask` endpoint, streams steps |
| Frontend | Next.js + TypeScript + Recharts | Chat UI, SQL view, chart, table |
| Tracing | LangSmith | Cost, latency, and step traces |
| Evals | pytest + custom scorer | Execution accuracy on a gold set |
| Deploy | AWS (App Runner or EC2) + Docker | Live demo link |
| Extra | MCP server | Exposes the agent's tools to any MCP client |

## Architecture: the agent graph

```
question
  -> classify     (is this answerable from the data? if not, say so)
  -> get_schema   (pick relevant tables and columns, with sample rows)
  -> write_sql    (generate SQL for the target dialect)
  -> validate     (sqlglot: SELECT only, known tables, add LIMIT)
  -> execute      (read-only connection, timeout)
  -> on error: repair_sql, back to validate (max 3 tries)
  -> pick_chart   (bar / line / table / single number)
  -> summarize    (plain-English answer, state assumptions and caveats)
```

State carried through the graph: question, chosen tables, SQL, attempts, error,
result rows, chart spec, final answer.

## Database layer

- One interface, two backends: `DuckDBWarehouse` and `SnowflakeWarehouse`.
  Switch with `WAREHOUSE=duckdb|snowflake` in `.env`.
- DuckDB dev data: `INSTALL tpch; LOAD tpch; CALL dbgen(sf=0.1);`
- Snowflake: use a dedicated read-only role and a small warehouse with auto-suspend.
- Schema context: table names, column names and types, and 3 sample rows per
  table. Add a short hand-written description per table in `semantic/tables.yaml`
  (business meaning of each table and key columns). This "semantic layer" is a
  big accuracy win.

## LLM provider layer

- One small interface (`backend/llm/`) with two implementations: Ollama and Anthropic.
  All agent nodes call the interface, never a provider directly.
- Default for development: `LLM_PROVIDER=ollama` with a coding model
  (for example `qwen2.5-coder:7b`), so building and testing costs nothing.
- Use Claude for final evals and the deployed demo.
- Evals must run on both providers and report accuracy, latency, and cost side
  by side. This comparison goes in the README ("cloud vs local tradeoff").

## Guardrails (required)

1. Read-only database credentials.
2. sqlglot rejects anything that is not a single SELECT (no INSERT, UPDATE,
   DELETE, DROP, multiple statements).
3. Only tables in the allowlist.
4. Auto-add `LIMIT 1000` if missing.
5. Query timeout (30s).
6. If the agent can't answer confidently, it says so instead of guessing.
7. Always show the SQL it ran, so users can verify.

## Evals (required)

- `evals/gold.yaml`: 40 questions, each with a hand-written gold SQL query.
  Mix of easy (single table), medium (joins, grouping), and hard (date math,
  window functions, ambiguous wording).
- Scorer: run agent SQL and gold SQL, compare result sets (order-insensitive,
  round floats). Report execution accuracy overall and by difficulty.
- Also track: average latency, average cost per question, repair attempts.
- `make eval` prints a summary table and saves results to `evals/results/`.

## Frontend

- Chat input, then a live view of the agent's steps as they stream.
- Result panel with tabs: Answer, Chart, Table, SQL.
- Example questions as clickable chips.
- Clean, simple styling. No auth needed for the demo.

## Project layout

```
backend/
  agent/        graph.py, nodes.py, prompts.py, state.py
  warehouse/    base.py, duckdb_wh.py, snowflake_wh.py
  guardrails/   sql_validator.py
  api/          main.py
  mcp_server.py
semantic/       tables.yaml
evals/          gold.yaml, run_evals.py, results/
frontend/       Next.js app
tests/
docker-compose.yml
README.md
.env.example
```

## Build phases

Build one phase at a time. Stop at the end of each phase so Melad can test it
and understand it before moving on.

**Phase 1: Core agent in the terminal (MVP)**
DuckDB with TPC-H, the LLM provider layer (Ollama first), schema context,
write_sql, validate, execute, repair loop, summarize. A CLI: `python -m backend.cli "top 5 customers by revenue"`.

**Phase 2: Evals and guardrails**
Full guardrail list, 40-question gold set, eval runner, LangSmith tracing.
Record the baseline score, then improve it (semantic layer, better prompts,
few-shot examples) and record the new score. The before/after number is the
headline result.

**Phase 3: API and frontend**
FastAPI `/ask` with streamed steps. Next.js + TypeScript UI with chart,
table, and SQL tabs.

**Phase 4: Snowflake**
`SnowflakeWarehouse` backend, read-only role, run evals against Snowflake too.

**Phase 5: MCP server and deploy**
MCP server exposing `list_tables`, `describe_table`, `run_query`, `ask`.
Dockerize and deploy to AWS. Live link in the README.

**Phase 6: Polish**
README with architecture diagram, eval results table, "business impact"
section, and setup steps. Record a 2-minute demo video.

## Rules

- Secrets only in `.env`. Commit `.env.example`, never `.env`.
- Keep costs low: small Snowflake warehouse, auto-suspend, cache schema context.
- Write tests for the SQL validator and warehouse layer.
- No em dashes in docs or UI text.
- After every Phase 2 fix, re-run the showcase questions and add an 'after' entry next to each 'before' entry in evals/showcase.md.
- Never overwrite `evals/results/baseline/`. Files there are frozen; new baseline files may only be added.
