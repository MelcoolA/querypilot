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
        self.prompts: list[str] = []  # every prompt received, for assertions

    def _complete(self, system: str, prompt: str) -> LLMResponse:
        self.prompts.append(prompt)
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
    # Every attempt is different but still broken, so all repairs are used.
    llm = FakeLLM([f"SELECT nope{i} FROM region" for i in range(MAX_REPAIRS + 1)])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["attempts"] == MAX_REPAIRS
    assert not state["repeated"]
    assert "could not answer" in state["answer"]


def test_stops_early_when_repair_repeats_itself(wh):
    # The repair returns the same broken SQL (different spacing and case).
    llm = FakeLLM(["SELECT nope FROM region", "select   nope\nfrom REGION"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["attempts"] == 1
    assert state["repeated"]
    assert "stopped early" in state["answer"]


def test_repair_prompt_lists_all_failed_attempts(wh):
    llm = FakeLLM(["SELECT nope1 FROM region", "SELECT nope2 FROM region", "SELECT count(*) FROM region"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert state["rows"] == [(5,)]
    second_repair_prompt = llm.prompts[2]
    assert "Attempt 1" in second_repair_prompt and "nope1" in second_repair_prompt
    assert "Attempt 2" in second_repair_prompt and "nope2" in second_repair_prompt


def test_canonical_sql_ignores_identifier_case_but_not_literals():
    from backend.agent.nodes import _canonical_sql

    tables = ["customer"]
    assert _canonical_sql("select C_NAME from CUSTOMER", tables, "duckdb") == \
        _canonical_sql("SELECT c_name FROM customer LIMIT 1000", tables, "duckdb")
    assert _canonical_sql("SELECT 1 FROM customer WHERE c_name = 'A'", tables, "duckdb") != \
        _canonical_sql("SELECT 1 FROM customer WHERE c_name = 'a'", tables, "duckdb")


def test_summary_flags_results_cut_off_at_row_limit(wh):
    llm = FakeLLM(["SELECT l_orderkey FROM lineitem"])  # far more than 1000 rows
    state = build_graph(llm, wh).invoke({"question": "list line items"})
    assert len(state["rows"]) == 1000
    assert "WARNING: the result hit the 1000-row limit" in llm.prompts[-1]
    assert "cut off at 1,000 rows" in state["answer"]


def test_summary_has_no_limit_note_for_small_results(wh):
    llm = FakeLLM(["SELECT count(*) AS n FROM region"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert "WARNING" not in llm.prompts[-1]
    assert "cut off" not in state["answer"]


def test_give_up_message_uses_singular_for_one_attempt(wh):
    llm = FakeLLM(["SELECT nope FROM region", "SELECT nope FROM region"])
    state = build_graph(llm, wh).invoke({"question": "how many regions?"})
    assert "After 1 repair attempt the query" in state["answer"]


def test_write_requests_get_a_clear_refusal(wh):
    llm = FakeLLM(["DELETE FROM region", "DELETE FROM region"])
    state = build_graph(llm, wh).invoke({"question": "delete all regions"})
    assert "only reads data" in state["answer"]
    assert wh.run_query("SELECT count(*) FROM region").rows == [(5,)]  # nothing was deleted
