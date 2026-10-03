from datetime import datetime
from decimal import Decimal

from backend.agent.facts import result_facts


def test_lowest_and_highest_with_their_labels():
    rows = [(datetime(2017, 1, 1), 800), (datetime(2017, 11, 1), 7544), (datetime(2017, 12, 1), 5673)]
    assert result_facts(["month", "orders"], rows) == [
        "rows: 3",
        "lowest orders: 800 (month 2017-01-01)",
        "highest orders: 7,544 (month 2017-11-01)",
    ]


def test_decimals_and_text_labels():
    rows = [("SP", Decimal("5202955.05")), ("PR", Decimal("683083.76"))]
    facts = result_facts(["state", "revenue"], rows)
    assert "lowest revenue: 683,083.76 (state PR)" in facts
    assert "highest revenue: 5,202,955.05 (state SP)" in facts


def test_nothing_for_single_rows_or_text_only_results():
    assert result_facts(["n"], [(96478,)]) == []
    assert result_facts(["state"], [("SP",), ("RJ",)]) == []


def test_booleans_are_labels_not_numbers():
    facts = result_facts(["is_late", "avg_score"], [(True, 2.57), (False, 4.29)])
    assert "lowest avg_score: 2.57 (is_late True)" in facts


def test_plain_dates_as_labels():
    from datetime import date

    facts = result_facts(["day", "orders"], [(date(2017, 1, 5), 3), (date(2017, 1, 6), 9)])
    assert "highest orders: 9 (day 2017-01-06)" in facts
