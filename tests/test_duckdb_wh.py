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


def test_slow_query_times_out():
    import time

    from backend.warehouse.base import QueryTimeoutError

    fast_timeout = DuckDBWarehouse(DB_PATH, timeout_s=0.5)
    start = time.time()
    with pytest.raises(QueryTimeoutError, match="timed out after 0.5s"):
        # A cross join of 600k x 600k rows would run for a very long time.
        fast_timeout.run_query("SELECT count(*) FROM lineitem a, lineitem b WHERE a.l_quantity < b.l_quantity")
    assert time.time() - start < 5


def test_connection_still_works_after_timeout():
    from backend.warehouse.base import QueryTimeoutError

    wh = DuckDBWarehouse(DB_PATH, timeout_s=0.5)
    with pytest.raises(QueryTimeoutError):
        wh.run_query("SELECT count(*) FROM lineitem a, lineitem b WHERE a.l_quantity < b.l_quantity")
    assert wh.run_query("SELECT count(*) FROM region").rows == [(5,)]


def test_default_timeout_is_30_seconds(wh):
    assert wh.timeout_s == 30
