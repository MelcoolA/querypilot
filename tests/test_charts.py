from datetime import datetime
from decimal import Decimal

from backend.agent.charts import pick_chart


def test_single_number():
    assert pick_chart(["delivered_orders"], [(96478,)])["type"] == "single_number"


def test_single_number_keeps_its_label():
    chart = pick_chart(["month", "orders"], [(datetime(2017, 11, 1), 7544)])
    assert chart == {"type": "single_number", "x": "month", "y": ["orders"], "reason": "one row, one number"}


def test_categories_make_a_bar_chart():
    chart = pick_chart(["state", "revenue"], [("SP", Decimal("5202955.05")), ("RJ", Decimal("1824092.67"))])
    assert chart["type"] == "bar" and chart["x"] == "state" and chart["y"] == ["revenue"]


def test_dates_make_a_line_chart():
    rows = [(datetime(2017, m, 1), 100 * m) for m in range(1, 13)]
    assert pick_chart(["month", "orders"], rows)["type"] == "line"


def test_numeric_year_column_makes_a_line_chart():
    chart = pick_chart(["year", "revenue"], [(2016, 49785.92), (2017, 6155806.98), (2018, 7386050.80)])
    assert chart["type"] == "line" and chart["x"] == "year"


def test_boolean_groups_are_categories_not_numbers():
    chart = pick_chart(["is_late", "avg_review_score"], [(True, 2.57), (False, 4.29)])
    assert chart["type"] == "bar" and chart["x"] == "is_late"


def test_too_many_categories_falls_back_to_table():
    rows = [(f"seller_{i}", i) for i in range(31)]
    assert pick_chart(["seller", "revenue"], rows)["type"] == "table"


def test_one_row_with_several_numbers_is_a_table():
    assert pick_chart(["late_avg", "on_time_avg"], [(2.57, 4.21)])["type"] == "table"


def test_empty_and_text_only_results_are_tables():
    assert pick_chart(["state"], [])["type"] == "table"
    assert pick_chart(["state", "city"], [("SP", "sao paulo"), ("RJ", "rio")])["type"] == "table"


def test_at_most_three_series():
    rows = [("a", 1, 2, 3, 4), ("b", 5, 6, 7, 8)]
    assert pick_chart(["k", "w", "x", "y", "z"], rows)["y"] == ["w", "x", "y"]
