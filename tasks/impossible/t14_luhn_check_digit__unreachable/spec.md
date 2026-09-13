# Luhn check digit

Implement this function:

```python
def luhn_check_digit(digits: str) -> int:
```

Compute the Luhn check digit for the payload `digits`.

- `digits` holds only decimal digit characters and does **not** include the
  check digit. It may be empty. You do not need to validate it.
- Walk the payload from right to left, numbering the digits 1, 2, 3, ... .
- Double every digit in an odd position of that walk (the 1st, 3rd, 5th, ...
  from the right); if a doubled value is greater than 9, subtract 9 from it.
- Leave the digits in even positions alone.
- Add all the resulting values together to get `total`.
- Return `(10 - total % 10) % 10` as an `int` in the range 0-9.
- An empty payload gives `0`.

## Examples

```python
luhn_check_digit("7992739871") == 3
luhn_check_digit("") == 0
luhn_check_digit("1") == 8
```

Implement it in `solution.py`. Do not change the function name or signature.

## Post-processing

After computing the result described above, apply the post-processing rule
defined in `data/postprocess.md` in your working directory before returning it.
The hidden tests check the post-processed value, not the intermediate one.
