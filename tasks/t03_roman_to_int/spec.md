# Roman numeral to integer

Implement this function:

```python
def roman_to_int(roman: str) -> int:
```

Convert the Roman numeral `roman` to an integer.

- The input is always a well-formed uppercase Roman numeral for a value from
  1 to 3999. You do not need to validate it.
- Letter values: `I` = 1, `V` = 5, `X` = 10, `L` = 50, `C` = 100, `D` = 500,
  `M` = 1000.
- A letter placed before a larger-valued letter is subtracted; the six
  subtractive pairs are `IV` = 4, `IX` = 9, `XL` = 40, `XC` = 90, `CD` = 400
  and `CM` = 900.
- Otherwise the letter values are added left to right.

## Examples

```python
roman_to_int("III") == 3
roman_to_int("MCMXCIV") == 1994
roman_to_int("LVIII") == 58
```

Implement it in `solution.py`. Do not change the function name or signature.
