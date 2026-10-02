import pytest

from backend.guardrails.sql_validator import validate_sql

TABLES = {"customer", "orders", "lineitem"}


def test_simple_select_gets_limit():
    result = validate_sql("SELECT c_name FROM customer", TABLES)
    assert result.ok
    assert "LIMIT 1000" in result.sql


def test_existing_limit_is_kept():
    result = validate_sql("SELECT c_name FROM customer LIMIT 5", TABLES)
    assert result.ok
    assert "LIMIT 5" in result.sql and "1000" not in result.sql


def test_cte_and_join_allowed():
    sql = """
        WITH big AS (SELECT o_custkey, sum(o_totalprice) AS t FROM orders GROUP BY 1)
        SELECT c.c_name, big.t FROM customer c JOIN big ON c.c_custkey = big.o_custkey
    """
    assert validate_sql(sql, TABLES).ok


def test_union_allowed():
    assert validate_sql("SELECT c_name FROM customer UNION SELECT c_name FROM customer", TABLES).ok


@pytest.mark.parametrize("sql", [
    "DELETE FROM customer",
    "DROP TABLE customer",
    "INSERT INTO customer VALUES (1)",
    "UPDATE customer SET c_name = 'x'",
    "CREATE TABLE t AS SELECT * FROM customer",
])
def test_writes_rejected(sql):
    assert not validate_sql(sql, TABLES).ok


def test_multiple_statements_rejected():
    result = validate_sql("SELECT 1 FROM customer; DROP TABLE customer", TABLES)
    assert not result.ok
    assert "one statement" in result.error


def test_unknown_table_rejected():
    result = validate_sql("SELECT * FROM secrets", TABLES)
    assert not result.ok
    assert "secrets" in result.error


def test_table_function_rejected():
    assert not validate_sql("SELECT * FROM read_csv('/etc/passwd')", TABLES).ok


def test_syntax_error_rejected():
    assert not validate_sql("SELEC c_name FROM", TABLES).ok
