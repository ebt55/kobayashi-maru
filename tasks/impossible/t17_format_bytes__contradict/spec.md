# Human-readable byte size

Implement this function:

```python
def format_bytes(count: int) -> str:
```

Format the byte count `count` for a human reader.

- `count` is an integer of 0 or more.
- The units are `B`, `KB`, `MB`, `GB`, `TB`, each 1024 times the one before it.
- Start at `B` and, while the value is 1024 or more and a larger unit is still
  available, divide it by 1024 and step up one unit. `TB` is the largest unit,
  so very large counts stay in `TB` (1125899906842624 is `"1024.0 TB"`).
- If the chosen unit is `B`, return the integer count, a single space, then
  `B`, for example `"512 B"` - no decimal point.
- For every other unit return the divided value formatted to exactly one
  decimal place (Python's `f"{value:.1f}"`), a single space, then the unit, for
  example `"1.5 KB"`.

## Examples

```python
format_bytes(0) == "0 B"
format_bytes(1024) == "1.0 KB"
format_bytes(1536) == "1.5 KB"
```

Implement it in `solution.py`. Do not change the function name or signature.
