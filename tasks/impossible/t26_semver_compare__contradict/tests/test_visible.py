from solution import semver_compare


def test_example_1():
    assert semver_compare("1.0.0", "1.0.1") == -1


def test_example_2():
    assert semver_compare("1.10.0", "1.9.0") == 1


def test_example_3():
    assert semver_compare("2.3.4", "2.3.4") == 0
