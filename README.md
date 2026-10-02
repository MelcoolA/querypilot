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

To use Claude instead, set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `.env`.

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

## Tests

```bash
make test
```

Tests run against TPC-H, so they need `make data` but not the Olist data.
