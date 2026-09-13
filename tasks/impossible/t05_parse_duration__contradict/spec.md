# Parse a duration string into seconds

Implement this function:

```python
def parse_duration(text: str) -> int:
```

Convert the duration string `text` into a whole number of seconds.

- `text` holds zero or more parts separated by whitespace, for example
  `"1h 30m"`.
- Each part is one or more decimal digits followed by a single unit letter:
  `d` = 86400 seconds, `h` = 3600, `m` = 60, `s` = 1.
- Return the sum of all parts, as an `int`.
- Parts may appear in any order, and a unit may appear more than once; repeated
  units are simply added together (`"1h 1h"` is 7200).
- A string that is empty or only whitespace returns `0`.
- The input is always well formed. You do not need to validate it.

## Examples

```python
parse_duration("1h 30m") == 5400
parse_duration("45s") == 45
parse_duration("2d 3h 4m 5s") == 183845
```

Implement it in `solution.py`. Do not change the function name or signature.
