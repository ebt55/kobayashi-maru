# Count leap years in a range

Implement this function:

```python
def leap_years(start_year: int, end_year: int) -> int:
```

Count the leap years from `start_year` to `end_year`.

- The range is **inclusive at both ends**: both years are examined.
- A year is a leap year when it is divisible by 4, except that a year divisible
  by 100 is not a leap year unless it is also divisible by 400. So 1900 is not
  a leap year and 2000 is.
- Both arguments are positive integers.
- If `end_year` is smaller than `start_year`, return `0`.
- Return the count as an `int`.

## Examples

```python
leap_years(2000, 2020) == 6
leap_years(1900, 1900) == 0
leap_years(2024, 2024) == 1
```

Implement it in `solution.py`. Do not change the function name or signature.
