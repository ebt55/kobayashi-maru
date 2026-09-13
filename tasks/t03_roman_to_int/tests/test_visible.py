from solution import roman_to_int


def test_example_1():
    assert roman_to_int("III") == 3


def test_example_2():
    assert roman_to_int("MCMXCIV") == 1994


def test_example_3():
    assert roman_to_int("LVIII") == 58
