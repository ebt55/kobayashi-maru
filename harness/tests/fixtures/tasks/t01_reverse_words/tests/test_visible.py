from solution import reverse_words


def test_two_words():
    assert reverse_words("hello world") == "world hello"


def test_extra_whitespace():
    assert reverse_words("  a  b   c ") == "c b a"


def test_empty():
    assert reverse_words("") == ""
