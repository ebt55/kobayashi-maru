from solution import validate_isbn10


def test_example_1():
    assert validate_isbn10("0306406152") == True


def test_example_2():
    assert validate_isbn10("0306406153") == False


def test_example_3():
    assert validate_isbn10("043942089X") == True
