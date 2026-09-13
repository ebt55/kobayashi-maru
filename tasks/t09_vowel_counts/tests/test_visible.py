from solution import vowel_counts


def test_example_1():
    assert vowel_counts("hello world") == {"hello": 2, "world": 1}


def test_example_2():
    assert vowel_counts("rhythm") == {"rhythm": 0}


def test_example_3():
    assert vowel_counts("") == {}
