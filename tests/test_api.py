"""API tests with a scripted fake LLM against the TPC-H test database."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.warehouse.duckdb_wh import DuckDBWarehouse
from tests.test_agent_graph import FakeLLM

DB_PATH = "data/tpch.duckdb"
pytestmark = pytest.mark.skipif(not Path(DB_PATH).exists(), reason="run `make data` first")


def client_with(sql_replies: list[str]) -> TestClient:
    return TestClient(create_app(llm=FakeLLM(sql_replies), warehouse=DuckDBWarehouse(DB_PATH)))


def events(response) -> list[tuple[str, dict]]:
    """Parse a Server-Sent Events body into (event name, data) pairs."""
    parsed = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        parsed.append((lines["event"], json.loads(lines["data"])))
    return parsed


def test_health_and_examples():
    client = client_with([])
    assert client.get("/health").json()["status"] == "ok"
    assert len(client.get("/examples").json()["questions"]) >= 3


def test_ask_streams_steps_then_result():
    response = client_with(["SELECT count(*) AS n FROM region"]).post("/ask", json={"question": "how many regions?"})
    assert response.headers["content-type"].startswith("text/event-stream")
    evs = events(response)
    steps = [data["node"] for name, data in evs if name == "step"]
    assert steps == ["get_schema", "write_sql", "validate", "execute", "pick_chart", "summarize"]
    name, result = evs[-1]
    assert name == "result"
    assert result["rows"] == [[5]]
    assert result["chart"]["type"] == "single_number"
    assert "SELECT" in result["sql"] and result["error"] == ""


def test_ask_reports_failure_without_rows_or_chart():
    evs = events(client_with(["SELECT nope FROM region"] * 2).post("/ask", json={"question": "how many regions?"}))
    steps = [data["node"] for name, data in evs if name == "step"]
    assert "repair_sql" in steps and "pick_chart" not in steps
    result = evs[-1][1]
    assert result["rows"] == [] and result["chart"] is None
    assert "could not answer" in result["answer"]


def test_decimals_and_dates_become_json():
    sql = "SELECT o_orderdate, o_totalprice FROM orders ORDER BY o_orderkey LIMIT 2"
    result = events(client_with([sql]).post("/ask", json={"question": "two orders"}))[-1][1]
    date_value, price = result["rows"][0]
    assert isinstance(date_value, str) and len(date_value) == 10  # ISO date
    assert isinstance(price, float)


def test_question_is_validated():
    assert client_with([]).post("/ask", json={"question": ""}).status_code == 422
