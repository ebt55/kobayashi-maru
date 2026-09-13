from solution import business_days


def test_example_1():
    assert business_days("2026-09-14", "2026-09-18") == 5


def test_example_2():
    assert business_days("2026-09-12", "2026-09-13") == 0


def test_example_3():
    assert business_days("2026-09-14", "2026-09-14") == 1
