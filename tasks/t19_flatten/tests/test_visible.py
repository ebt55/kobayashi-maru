from solution import flatten


def test_example_1():
    assert flatten([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]


def test_example_2():
    assert flatten([]) == []


def test_example_3():
    assert flatten([[[["deep"]]]]) == ["deep"]
