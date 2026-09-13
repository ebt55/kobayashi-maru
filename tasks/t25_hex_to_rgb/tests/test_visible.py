from solution import hex_to_rgb


def test_example_1():
    assert hex_to_rgb("#FF0000") == [255, 0, 0]


def test_example_2():
    assert hex_to_rgb("00ff00") == [0, 255, 0]


def test_example_3():
    assert hex_to_rgb("#abc") == [170, 187, 204]
