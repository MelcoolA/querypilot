.PHONY: data test ask

# Build the local TPC-H database (scale factor 0.1, about 25 MB)
data:
	python -m backend.warehouse.setup_duckdb

test:
	python -m pytest -q

ask:
	python -m backend.cli "$(Q)"
