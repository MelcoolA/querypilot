.PHONY: data data-olist data-snowflake test ask eval api ui mcp up down

# Build the local TPC-H database (scale factor 0.1, about 25 MB)
data:
	python -m backend.warehouse.setup_duckdb

# Build the Olist e-commerce database from the CSVs in data/olist/
data-olist:
	python -m backend.warehouse.setup_olist

# Load the Olist tables into Snowflake (needs snowflake/loader_user.sql run first)
data-snowflake:
	python -m backend.warehouse.setup_snowflake

test:
	python -m pytest -q

ask:
	python -m backend.cli "$(Q)"

# Run the agent on all gold questions and save results to evals/results/
eval:
	python -m evals.run_evals

# Run the API on http://localhost:8000 (docs at /docs)
api:
	uvicorn --factory backend.api.main:create_app --reload --port 8000

# Run the web UI on http://localhost:3000 (needs `make api` running too)
ui:
	cd frontend && npm run dev

# Run the MCP server over stdio (normally started by an MCP client, not by hand)
mcp:
	python -m backend.mcp_server

# Run everything in Docker (API + UI): http://localhost:3000
up:
	docker compose up --build -d
	@echo "Starting: UI at http://localhost:3000, API at http://localhost:8000 (first start loads the model, about 1 to 2 minutes)"

down:
	docker compose down
