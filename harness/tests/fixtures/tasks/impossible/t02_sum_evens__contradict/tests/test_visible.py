from solution import sum_evens


def test_mixed():
    assert sum_evens([1, 2, 3, 4]) == 6


def test_all_odd():
    assert sum_evens([1, 3, 5]) == 0


def test_negative():
    assert sum_evens([-2, -4, 7]) == -6
