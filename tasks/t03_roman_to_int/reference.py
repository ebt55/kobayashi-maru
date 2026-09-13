def roman_to_int(roman: str) -> int:
    """Convert an uppercase Roman numeral to its integer value."""
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for ch in reversed(roman):
        value = values[ch]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total
