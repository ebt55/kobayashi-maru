def sum_evens(numbers: list) -> int:
    """Return the sum of the even integers in ``numbers``."""
    return sum(n for n in numbers if n % 2 == 0)
