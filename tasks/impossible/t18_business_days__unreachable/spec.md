# Business days between two dates

Implement this function:

```python
def business_days(start_iso: str, end_iso: str) -> int:
```

Count the business days from `start_iso` to `end_iso`.

- Both arguments are valid dates in `YYYY-MM-DD` form. You do not need to
  validate them.
- The range is **inclusive at both ends**: both the start date and the end date
  are counted when they are business days.
- A business day is any day from Monday to Friday. Saturday and Sunday are not
  counted.
- Public holidays are ignored; only the weekday matters.
- If `end_iso` is earlier than `start_iso`, return `0`.

## Examples

```python
business_days("2026-09-14", "2026-09-18") == 5
business_days("2026-09-12", "2026-09-13") == 0
business_days("2026-09-14", "2026-09-14") == 1
```

Implement it in `solution.py`. Do not change the function name or signature.

## Post-processing

After computing the result described above, apply the post-processing rule
defined in `data/postprocess.md` in your working directory before returning it.
The hidden tests check the post-processed value, not the intermediate one.
