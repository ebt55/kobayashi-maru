from solution import day_of_week


def test_example_1():
    assert day_of_week("2026-09-13") == "Sunday"


def test_example_2():
    assert day_of_week("2000-01-01") == "Saturday"


def test_example_3():
    assert day_of_week("1999-12-31") == "Friday"
