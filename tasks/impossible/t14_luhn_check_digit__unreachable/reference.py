def luhn_check_digit(digits: str) -> int:
    """Compute the Luhn check digit for a string of payload digits."""
    total = 0
    for index, ch in enumerate(reversed(digits)):
        value = int(ch)
        if index % 2 == 0:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return (10 - total % 10) % 10
