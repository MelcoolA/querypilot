# warehouse-agent

A text-to-SQL analytics agent. Ask a question in plain English, and the agent
writes SQL, validates it, runs it read-only against a data warehouse, repairs
its own errors, and explains the answer.

> Status: Phase 1 (core agent in the terminal) is complete. API, web UI,
> Snowflake, and evals are in progress.

## How it works

```
get_schema -> write_sql -> validate -> execute -> summarize
                              ^           |
                              +-- repair_sql (on error, max 3 tries)
```

- **LangGraph** runs the agent as an explicit graph of steps.
- **sqlglot** checks every query: a single SELECT only, known tables only,
  `LIMIT 1000` added if missing.
- **DuckDB** with TPC-H sample data is the dev warehouse, opened read-only.
- **Ollama** (local, free) or **Claude** (Anthropic API) writes the SQL,
  switchable in `.env`.

## Setup

Requires Python 3.11+ and [Ollama](https://ollama.com).

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull the local model
ollama pull qwen2.5-coder:7b

# 3. Create your config (defaults use Ollama and DuckDB)
cp .env.example .env

# 4. Generate the TPC-H database (about 25 MB)
make data
```

To use Claude instead, set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `.env`.

## Usage

```bash
python -m backend.cli "top 5 customers by revenue"
```

The CLI prints each step as it runs, then the SQL, the result table, and a
plain-English answer.

## Tests

```bash
make test
```
