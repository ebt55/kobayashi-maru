def running_average(values: list) -> list:
    """Return the cumulative mean after each element, rounded to two decimals."""
    averages = []
    total = 0
    for index, value in enumerate(values, start=1):
        total += value
        averages.append(round(total / index, 2))
    return averages
