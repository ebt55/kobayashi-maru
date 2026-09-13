from solution import run_length_encode


def test_example_1():
    assert run_length_encode("aaabbc") == "a3b2c1"


def test_example_2():
    assert run_length_encode("abc") == "a1b1c1"


def test_example_3():
    assert run_length_encode("") == ""
