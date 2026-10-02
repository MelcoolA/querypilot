"""Run the full graph with a scripted fake LLM, so the repair loop is tested deterministically."""
from pathlib import Path

import pytest

from backend.agent.graph import MAX_REPAIRS, build_graph
from backend.llm import LLM, LLMResponse
from backend.warehouse.duckdb_wh import DuckDBWarehouse

DB_PATH = "data/tpch.duckdb"
pytestmark = pytest.mark.skipif(not Path(DB_PATH).exists(), reason="run `make data` first")


class FakeLLM(LLM):
    name = "fake"

    def __init__(self, sql_replies: list[str]):
        self.sql_replies = list(sql_replies)

    def complete(self, system: str, prompt: str) -> LLMResponse:
        if "explain data results" in system:  # the summarize prompt
            return LLMResponse("There are 5 regions.")
        return LLMResponse(f"```sql\n{self.sql_replies.pop(0)}\n```")


@pytest.fixture(scope="module")
def wh():
    return DuckDBWarehouse(DB_PATH)


def test_happy_path(wh):
    agent = build_graph(FakeLLM(["SELECT count(*) AS n FROM region"]), wh)
    state = agent.invoke({"question": "how many regions?"})
    assert state["rows"] == [(5,)]
    assert state["attempts"] == 0
    assert state["answer"] == "There are 5 regions."


def test_repairs_execution_error(wh):
    # First SQL uses a column that does not exist; the repair fixes it.
    llm = FakeLLM(["SELECT count(region_id) FROM region", "SELECT count(*) AS n FROM region"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["attempts"] == 1
    assert state["rows"] == [(5,)]


def test_repairs_validation_error(wh):
    llm = FakeLLM(["DROP TABLE region", "SELECT count(*) AS n FROM region"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["attempts"] == 1
    assert state["rows"] == [(5,)]


def test_gives_up_after_max_repairs(wh):
    llm = FakeLLM(["SELECT nope FROM region"] * (MAX_REPAIRS + 1))
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["attempts"] == MAX_REPAIRS
    assert "could not answer" in state["answer"]
