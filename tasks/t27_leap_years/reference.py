def leap_years(start_year: int, end_year: int) -> int:
    """Count the Gregorian leap years in an inclusive year range."""
    count = 0
    for year in range(start_year, end_year + 1):
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            count += 1
    return count
