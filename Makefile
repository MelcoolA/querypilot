.PHONY: data data-olist test ask eval

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
