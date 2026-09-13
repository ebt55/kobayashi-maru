def validate_isbn10(code: str) -> bool:
    """Return True when a string is a valid ISBN-10."""
    cleaned = code.replace("-", "").replace(" ", "")
    if len(cleaned) != 10:
        return False
    total = 0
    for index, ch in enumerate(cleaned):
        if ch.isdigit():
            value = int(ch)
        elif ch in "Xx" and index == 9:
            value = 10
        else:
            return False
        total += value * (10 - index)
    return total % 11 == 0
