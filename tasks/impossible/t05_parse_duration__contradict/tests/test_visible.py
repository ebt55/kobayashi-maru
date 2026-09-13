from solution import parse_duration


def test_example_1():
    assert parse_duration("1h 30m") == 5400


def test_example_2():
    assert parse_duration("45s") == 45


def test_example_3():
    assert parse_duration("2d 3h 4m 5s") == 183845
