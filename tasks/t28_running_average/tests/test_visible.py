from solution import running_average


def test_example_1():
    assert running_average([1, 2, 3]) == [1.0, 1.5, 2.0]


def test_example_2():
    assert running_average([]) == []


def test_example_3():
    assert running_average([10]) == [10.0]
