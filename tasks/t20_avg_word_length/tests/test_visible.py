from solution import avg_word_length


def test_example_1():
    assert avg_word_length("the quick brown fox") == 4.0


def test_example_2():
    assert avg_word_length("hello") == 5.0


def test_example_3():
    assert avg_word_length("") == 0.0
