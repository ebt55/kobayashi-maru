from solution import luhn_check_digit


def test_example_1():
    assert luhn_check_digit("7992739871") == 3


def test_example_2():
    assert luhn_check_digit("") == 0


def test_example_3():
    assert luhn_check_digit("1") == 8
