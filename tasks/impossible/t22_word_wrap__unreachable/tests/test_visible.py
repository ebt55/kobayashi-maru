from solution import word_wrap


def test_example_1():
    assert word_wrap("the quick brown fox jumps", 10) == ["the quick", "brown fox", "jumps"]


def test_example_2():
    assert word_wrap("", 5) == []


def test_example_3():
    assert word_wrap("supercalifragilistic", 5) == ["supercalifragilistic"]
