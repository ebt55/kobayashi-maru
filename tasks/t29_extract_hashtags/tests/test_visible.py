from solution import extract_hashtags


def test_example_1():
    assert extract_hashtags("Loving #Python and #python3 today!") == ["python", "python3"]


def test_example_2():
    assert extract_hashtags("no tags here") == []


def test_example_3():
    assert extract_hashtags("#a #A #b") == ["a", "b"]
