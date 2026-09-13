def char_frequency(text: str) -> dict:
    """Count each ASCII letter of a string, case-insensitively."""
    counts = {}
    for ch in text.lower():
        if "a" <= ch <= "z":
            counts[ch] = counts.get(ch, 0) + 1
    return counts
