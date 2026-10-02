"""The semantic layer must only refer to tables and columns that really exist."""
import re
from pathlib import Path

import pytest

from backend.agent import nodes
from backend.agent.semantic import load_semantic
from backend.warehouse.duckdb_wh import DuckDBWarehouse

OLIST_DB = "data/olist.duckdb"


@pytest.fixture(scope="module")
def olist():
    if not Path(OLIST_DB).exists():
        pytest.skip("run `make data-olist` first")
    return DuckDBWarehouse(OLIST_DB, dataset="olist")


def test_tables_and_columns_exist(olist):
    sem = load_semantic("olist")
    real_tables = set(olist.list_tables())
    for table, spec in sem["tables"].items():
        assert table in real_tables, f"unknown table {table}"
        real_cols = {c for c, _ in olist.describe_table(table).columns}
        for col in (spec.get("columns") or {}):
            assert col in real_cols, f"unknown column {table}.{col}"


def test_join_paths_exist(olist):
    for join in load_semantic("olist")["joins"]:
        for table, col in re.findall(r"(\w+)\.(\w+)", join):
            assert col in {c for c, _ in olist.describe_table(table).columns}, join


def test_schema_context_includes_semantics(olist):
    ctx = nodes.get_schema({}, olist)["schema_context"]
    assert ctx.startswith("BUSINESS DEFINITIONS")
    assert "'health_beauty'" in ctx  # list_values pulled from the data


def test_dataset_without_semantic_layer_is_unchanged():
    assert load_semantic("tpch") is None
    assert load_semantic("") is None
