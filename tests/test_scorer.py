from datetime import datetime
from decimal import Decimal

from evals.scorer import results_match


def ok(gold, agent):
    return results_match(gold, agent)[0]


def test_exact_match_any_order():
    assert ok([("SP", 10), ("RJ", 5)], [("RJ", 5), ("SP", 10)])


def test_floats_rounded_and_types_mixed():
    assert ok([(4.0862,)], [(Decimal("4.09"),)])
    assert ok([(96478,)], [(96478.0,)])


def test_wrong_number_fails():
    assert not ok([("SP", 40302)], [("SP", 41746)])


def test_column_names_and_order_ignored_extra_columns_allowed():
    gold = [("health_beauty", 1258681.34)]
    agent = [(1258681.34, 9670, "health_beauty")]
    assert ok(gold, agent)


def test_missing_gold_column_fails():
    assert not ok([("SP", 40302)], [("SP",)])


def test_row_count_must_match():
    assert not ok([("SP", 1)], [("SP", 1), ("RJ", 2)])


def test_month_formats_equal():
    gold = [(datetime(2017, 11, 1), 7544)]
    assert ok(gold, [("2017-11", 7544)])
    assert ok(gold, [("2017-11-01 00:00:00", 7544)])


def test_boolean_label_column_not_compared():
    gold = [(True, 2.57), (False, 4.29)]
    assert ok(gold, [("late", 2.57), ("on time", 4.29)])
    assert not ok(gold, [("late", 2.57), ("on time", 4.30)])


def test_rows_must_pair_correctly():
    # Same column values, but states and counts are swapped between rows.
    assert not ok([("SP", 10), ("RJ", 5)], [("SP", 5), ("RJ", 10)])


def test_nulls_compare_equal():
    assert ok([(None, 3)], [(None, 3)])
