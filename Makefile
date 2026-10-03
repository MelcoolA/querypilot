.PHONY: data data-olist test ask eval api ui

# Build the local TPC-H database (scale factor 0.1, about 25 MB)
data:
	python -m backend.warehouse.setup_duckdb

# Build the Olist e-commerce database from the CSVs in data/olist/
data-olist:
	python -m backend.warehouse.setup_olist

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
