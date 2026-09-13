from solution import merge_intervals


def test_example_1():
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]


def test_example_2():
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]


def test_example_3():
    assert merge_intervals([]) == []
