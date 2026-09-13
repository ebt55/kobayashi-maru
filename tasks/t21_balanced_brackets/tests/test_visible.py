from solution import balanced_brackets


def test_example_1():
    assert balanced_brackets("(a[b]{c})") == True


def test_example_2():
    assert balanced_brackets("([)]") == False


def test_example_3():
    assert balanced_brackets("") == True
