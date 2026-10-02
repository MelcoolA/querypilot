from pathlib import Path

import duckdb
import pytest

from backend.warehouse.duckdb_wh import DuckDBWarehouse

DB_PATH = "data/tpch.duckdb"
pytestmark = pytest.mark.skipif(not Path(DB_PATH).exists(), reason="run `make data` first")


@pytest.fixture(scope="module")
def wh():
    return DuckDBWarehouse(DB_PATH)


def test_lists_tpch_tables(wh):
    assert set(wh.list_tables()) == {
        "customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier",
    }


def test_describe_table_has_columns_and_samples(wh):
    info = wh.describe_table("region")
    assert ("r_name", "VARCHAR") in info.columns
    assert len(info.sample.rows) == 3


def test_describe_unknown_table_raises(wh):
    with pytest.raises(ValueError):
        wh.describe_table("not_a_table")


def test_run_query(wh):
    result = wh.run_query("SELECT count(*) AS n FROM region")
    assert result.columns == ["n"]
    assert result.rows == [(5,)]


def test_connection_is_read_only(wh):
    with pytest.raises(duckdb.Error):
        wh.run_query("DELETE FROM region")
