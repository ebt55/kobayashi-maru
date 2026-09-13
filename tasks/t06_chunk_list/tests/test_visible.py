from solution import chunk_list


def test_example_1():
    assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_example_2():
    assert chunk_list(["a", "b", "c"], 3) == [["a", "b", "c"]]


def test_example_3():
    assert chunk_list([], 4) == []
