# Hex colour to RGB

Implement this function:

```python
def hex_to_rgb(color: str) -> list:
```

Convert the hex colour `color` into its red, green and blue components.

- `color` may start with a `#`; if it does, ignore that character.
- What is left is either 6 hex digits (`"0d1e2f"`) or the 3-digit shorthand
  (`"0d1"`), in upper or lower case. You do not need to validate it.
- In the shorthand form each digit is doubled first, so `"abc"` means
  `"aabbcc"`.
- Read the 6 digits as three pairs and convert each pair from base 16.
- Return a list of exactly three integers in the range 0-255, in red, green,
  blue order. Use a list, not a tuple.

## Examples

```python
hex_to_rgb("#FF0000") == [255, 0, 0]
hex_to_rgb("00ff00") == [0, 255, 0]
hex_to_rgb("#abc") == [170, 187, 204]
```

Implement it in `solution.py`. Do not change the function name or signature.
