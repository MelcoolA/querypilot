"""MCP server tests: tool functions directly, then the real server over stdio."""
import asyncio
import json
import sys
from pathlib import Path

import pytest

from backend import mcp_server
from backend.agent.graph import build_graph
from backend.warehouse.duckdb_wh import DuckDBWarehouse
from tests.test_agent_graph import FakeLLM

TPCH = "data/tpch.duckdb"
OLIST = "data/olist.duckdb"


@pytest.fixture
def tools(monkeypatch):
    """Point the tools at the TPC-H test database and a scripted fake LLM."""
    if not Path(TPCH).exists():
        pytest.skip("run `make data` first")
    wh = DuckDBWarehouse(TPCH)
    monkeypatch.setattr(mcp_server, "_warehouse", lambda: wh)
    monkeypatch.setattr(mcp_server, "_agent", lambda: build_graph(FakeLLM(["SELECT count(*) AS n FROM region"]), wh))
    return mcp_server


def test_list_and_describe_tables(tools):
    names = [t["table"] for t in tools.list_tables()]
    assert "region" in names and len(names) == 8
    desc = tools.describe_table("region")
    assert [c["name"] for c in desc["columns"]][:2] == ["r_regionkey", "r_name"]
    assert len(desc["sample_rows"]) == 3


def test_describe_unknown_table_is_an_error(tools):
    with pytest.raises(ValueError, match="Unknown table"):
        tools.describe_table("secrets")


def test_run_query_adds_limit_and_caps_rows(tools):
    result = tools.run_query("SELECT l_orderkey FROM lineitem")
    assert "LIMIT 1000" in result["sql"]
    assert result["row_count"] == 1000 and len(result["rows"]) == 100 and result["truncated"]


@pytest.mark.parametrize("sql", ["DELETE FROM region", "DROP TABLE region", "SELECT * FROM read_csv('/etc/passwd')"])
def test_run_query_guardrails(tools, sql):
    with pytest.raises(ValueError, match="guardrail"):
        tools.run_query(sql)


def test_ask_runs_the_agent(tools):
    result = tools.ask("how many regions?")
    assert result["succeeded"] and result["rows"] == [{"n": 5}]
    assert result["chart"] == "single_number" and "SELECT" in result["sql"]


@pytest.mark.skipif(not Path(OLIST).exists(), reason="run `make data-olist` first")
def test_real_server_over_stdio():
    """Start the server as a subprocess, the way an MCP client does, and call it."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def session_calls():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "backend.mcp_server"],
            env={"WAREHOUSE": "duckdb", "DATASET": "olist", "LANGSMITH_TRACING": "false"},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            count = await session.call_tool("run_query", {"sql": "SELECT COUNT(*) AS n FROM orders"})
            blocked = await session.call_tool("run_query", {"sql": "DELETE FROM orders"})
            return listed, count, blocked

    listed, count, blocked = asyncio.run(session_calls())
    assert {t.name for t in listed.tools} == {"list_tables", "describe_table", "run_query", "ask"}
    assert all(t.annotations.read_only_hint for t in listed.tools)
    assert not count.is_error
    payload = count.structured_content or json.loads(count.content[0].text)
    assert payload["rows"] == [{"n": 99441}]
    assert blocked.is_error
