from solution import dedupe


def test_example_1():
    assert dedupe([1, 2, 1, 3, 2]) == [1, 2, 3]


def test_example_2():
    assert dedupe(["a", "b", "a"]) == ["a", "b"]


def test_example_3():
    assert dedupe([]) == []
