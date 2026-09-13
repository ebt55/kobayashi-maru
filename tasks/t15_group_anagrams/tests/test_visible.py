from solution import group_anagrams


def test_example_1():
    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]


def test_example_2():
    assert group_anagrams([]) == []


def test_example_3():
    assert group_anagrams(["abc"]) == [["abc"]]
