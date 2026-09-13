from solution import caesar_shift


def test_example_1():
    assert caesar_shift("abc", 1) == "bcd"


def test_example_2():
    assert caesar_shift("Hello, World!", 3) == "Khoor, Zruog!"


def test_example_3():
    assert caesar_shift("xyz", 3) == "abc"
