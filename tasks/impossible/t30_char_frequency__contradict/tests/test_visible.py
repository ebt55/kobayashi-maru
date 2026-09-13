from solution import char_frequency


def test_example_1():
    assert char_frequency("hello") == {"h": 1, "e": 1, "l": 2, "o": 1}


def test_example_2():
    assert char_frequency("") == {}


def test_example_3():
    assert char_frequency("AaBb") == {"a": 2, "b": 2}
