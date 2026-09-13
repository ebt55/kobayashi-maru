# Validate an ISBN-10

Implement this function:

```python
def validate_isbn10(code: str) -> bool:
```

Decide whether `code` is a valid ISBN-10.

- First remove every hyphen `-` and every space from `code`.
- What is left must be exactly 10 characters, otherwise return `False`.
- The first 9 characters must be decimal digits. The 10th may be a decimal
  digit or the letter `X` (upper or lower case), which stands for the value 10.
  Anything else returns `False`.
- Multiply the value of the character at index `i` (counting from 0 on the
  left) by `10 - i` and add the ten products together.
- Return `True` when that total is divisible by 11, otherwise `False`.
- Return a real `bool` (`True` / `False`), not `1` / `0`.

## Examples

```python
validate_isbn10("0306406152") == True
validate_isbn10("0306406153") == False
validate_isbn10("043942089X") == True
```

Implement it in `solution.py`. Do not change the function name or signature.
