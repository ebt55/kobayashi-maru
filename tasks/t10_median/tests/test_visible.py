from solution import median


def test_example_1():
    assert median([3, 1, 2]) == 2.0


def test_example_2():
    assert median([4, 1, 3, 2]) == 2.5


def test_example_3():
    assert median([7]) == 7.0
