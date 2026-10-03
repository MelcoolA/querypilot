from backend.formatting import describe_step


def test_row_count_is_singular_for_one_row():
    assert describe_step("execute", {"rows": [(1,)]}) == "1 row"
    assert describe_step("execute", {"rows": [(1,), (2,)]}) == "2 rows"
    assert describe_step("execute", {"rows": []}) == "0 rows"


def test_chart_type_is_readable():
    assert describe_step("pick_chart", {"chart": {"type": "single_number"}}) == "single number"
