# ISO date to weekday name

Implement this function:

```python
def day_of_week(iso_date: str) -> str:
```

Return the weekday of the date `iso_date`.

- `iso_date` is always a valid date in `YYYY-MM-DD` form (proleptic Gregorian
  calendar). You do not need to validate it.
- Return the English weekday name, capitalised, exactly one of: `"Monday"`,
  `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`,
  `"Sunday"`.
- Do not abbreviate and do not use the locale: the names above are literal.

## Examples

```python
day_of_week("2026-09-13") == "Sunday"
day_of_week("2000-01-01") == "Saturday"
day_of_week("1999-12-31") == "Friday"
```

Implement it in `solution.py`. Do not change the function name or signature.
