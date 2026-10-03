"""Integration tests against the real Snowflake account.

They need network access and use a little warehouse time, so they only run
when asked:  RUN_SNOWFLAKE_TESTS=1 python -m pytest tests/test_snowflake.py
"""
import os
from collections import Counter

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_SNOWFLAKE_TESTS") != "1", reason="set RUN_SNOWFLAKE_TESTS=1")


@pytest.fixture(scope="module")
def sf():
    from backend.warehouse.snowflake_wh import SnowflakeWarehouse

    return SnowflakeWarehouse()


@pytest.fixture(scope="module")
def duck():
    from backend.warehouse.duckdb_wh import DuckDBWarehouse

    return DuckDBWarehouse("data/olist.duckdb", dataset="olist")


def test_same_tables_and_columns_as_duckdb(sf, duck):
    assert sf.list_tables() == duck.list_tables()
    for table in duck.list_tables():
        assert [c for c, _ in sf.describe_table(table).columns] == [c for c, _ in duck.describe_table(table).columns]


def test_agent_role_is_read_only(sf):
    from snowflake.connector.errors import ProgrammingError

    for sql in ["CREATE TABLE should_fail (x INT)", "DELETE FROM orders"]:
        with pytest.raises(ProgrammingError):
            sf.run_query(sql)


def test_slow_query_times_out(sf):
    from backend.warehouse.base import QueryTimeoutError
    from backend.warehouse.snowflake_wh import SnowflakeWarehouse

    fast = SnowflakeWarehouse(timeout_s=2)
    # SYSTEM$WAIT sleeps; a big cross join is not slow enough here (Snowflake
    # finished a 112k x 112k join in 0.2s and caches results).
    with pytest.raises(QueryTimeoutError):
        fast.run_query("SELECT SYSTEM$WAIT(10)")


def test_translated_examples_match_duckdb(sf, duck):
    """Every worked example, translated to Snowflake SQL, gives DuckDB's answer."""
    from backend.agent.semantic import load_semantic, to_dialect
    from evals.scorer import results_match

    for example in load_semantic("olist")["examples"]:
        expected = duck.run_query(example["sql"]).rows
        actual = sf.run_query(to_dialect(example["sql"], "snowflake")).rows
        match, reason = results_match(expected, actual)
        assert match, f"{example['question']}: {reason}"
