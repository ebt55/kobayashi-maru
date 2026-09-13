from solution import normalize_whitespace


def test_example_1():
    assert normalize_whitespace("  hello   world  ") == "hello world"


def test_example_2():
    assert normalize_whitespace("a\tb\nc") == "a b c"


def test_example_3():
    assert normalize_whitespace("   ") == ""
