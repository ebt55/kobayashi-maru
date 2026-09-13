from solution import top_k_tokens


def test_example_1():
    assert top_k_tokens("the cat the dog the bird", 2) == ["the", "bird"]


def test_example_2():
    assert top_k_tokens("a b c", 5) == ["a", "b", "c"]


def test_example_3():
    assert top_k_tokens("", 3) == []
