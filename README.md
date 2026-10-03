# warehouse-agent

A text-to-SQL analytics agent. Ask a question in plain English, and the agent
writes SQL, validates it, runs it read-only against a data warehouse, repairs
its own errors, and explains the answer.

> Status: the core agent (Phase 1) and evals with a semantic layer (Phase 2)
> work in the terminal. API, web UI, and Snowflake are next.

## How it works

```
get_schema -> write_sql -> validate -> execute -> summarize
                              ^           |
                              +-- repair_sql (on error, max 3 tries)
```

- **LangGraph** runs the agent as an explicit graph of steps.
- **sqlglot** checks every query: a single SELECT only, known tables only,
  `LIMIT 1000` added if missing.
- **DuckDB** is the dev warehouse, opened read-only, with two datasets:
  TPC-H (synthetic benchmark data) and Olist (real Brazilian e-commerce data).
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

### Choosing the LLM

Both providers are set in `.env`; no code changes needed.

| Setting | Ollama (local, free) | Claude (Anthropic API) |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `anthropic` |
| Model | `OLLAMA_MODEL=qwen2.5-coder:7b` | `ANTHROPIC_MODEL=<model id>` |
| Other | `OLLAMA_NUM_CTX=16384` | `ANTHROPIC_API_KEY=<your key>` |

`OLLAMA_NUM_CTX` matters: Ollama's default context is 4,096 tokens, and it
silently drops part of any longer prompt. The Olist prompt (schema, semantic
layer, examples) is about 5,000 tokens, so without this setting the model
never sees the business definitions.

### Optional: Olist e-commerce dataset

[Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) is about
100k real orders from a Brazilian marketplace (2016 to 2018), with customers,
payments, reviews, products, and sellers. Its messier, more realistic business
questions make it a harder test than TPC-H.

1. Download the dataset from Kaggle and unzip the 9 CSV files into `data/olist/`.
2. Build the database:

   ```bash
   make data-olist
   ```

3. Set `DATASET=olist` in `.env` (or `DATASET=tpch` to switch back).

The load script cleans the data so the agent sees a tidy schema:

- Short table names (`olist_orders_dataset.csv` becomes `orders`)
- Date columns stored as timestamps
- English category names joined into `products.product_category`
- Geolocation reduced to one row per zip code prefix, so joins don't
  multiply rows

## Usage

```bash
python -m backend.cli "top 5 customers by revenue"
```

The CLI prints each step as it runs, then the SQL, the result table, and a
plain-English answer.

To ask about one dataset without editing `.env`:

```bash
DATASET=olist python -m backend.cli "How many orders were delivered?"
```

## Evals

The eval runs the agent on 40 Olist questions (12 easy, 16 medium, 12 hard)
and compares each result with a hand-written gold query. It needs the Olist
database (`make data-olist`) and uses whichever LLM `.env` selects.

```bash
make eval                                   # all 40 questions
python -m evals.run_evals --ids e01,m03     # a few questions, for quick checks
python -m evals.rescore evals/results/<run> # re-score a saved run (no LLM calls)
```

Each run prints accuracy (overall, by difficulty, by trap), latency, tokens,
cost, and repairs, and saves `results.json` and `summary.md` to
`evals/results/<date>_<model>/`. The change-by-change history is in
`evals/CHANGELOG.md`.

## Tests

```bash
make test
```

Most tests run against TPC-H and need `make data`. The semantic layer tests
use Olist and are skipped if `make data-olist` hasn't been run.
