from solution import slugify


def test_example_1():
    assert slugify("Hello, World!") == "hello-world"


def test_example_2():
    assert slugify("  Python 3.12 Rocks  ") == "python-3-12-rocks"


def test_example_3():
    assert slugify("---") == ""
