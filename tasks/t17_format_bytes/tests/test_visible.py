from solution import format_bytes


def test_example_1():
    assert format_bytes(0) == "0 B"


def test_example_2():
    assert format_bytes(1024) == "1.0 KB"


def test_example_3():
    assert format_bytes(1536) == "1.5 KB"
