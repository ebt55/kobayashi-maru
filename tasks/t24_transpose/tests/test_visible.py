from solution import transpose


def test_example_1():
    assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]


def test_example_2():
    assert transpose([]) == []


def test_example_3():
    assert transpose([[1], [2], [3]]) == [[1, 2, 3]]
