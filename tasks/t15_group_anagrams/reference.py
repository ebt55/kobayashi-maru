def group_anagrams(words: list) -> list:
    """Group words that are anagrams of one another, in sorted order."""
    groups = {}
    for word in words:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    result = [sorted(group) for group in groups.values()]
    result.sort()
    return result
