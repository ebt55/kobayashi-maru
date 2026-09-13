from solution import leap_years


def test_example_1():
    assert leap_years(2000, 2020) == 6


def test_example_2():
    assert leap_years(1900, 1900) == 0


def test_example_3():
    assert leap_years(2024, 2024) == 1
