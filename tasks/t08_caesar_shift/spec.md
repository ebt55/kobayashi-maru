# Caesar shift a string

Implement this function:

```python
def caesar_shift(text: str, shift: int) -> str:
```

Apply a Caesar shift of `shift` positions to `text`.

- Shift each ASCII letter forward through the alphabet, wrapping from `z` back
  to `a` and from `Z` back to `A`.
- Case is preserved: lowercase letters stay lowercase, uppercase stay
  uppercase.
- Every character that is not an ASCII letter (digits, spaces, punctuation,
  anything else) is copied through unchanged.
- `shift` may be `0`, negative, or larger than 26; reduce it modulo 26, so a
  shift of 27 behaves like a shift of 1 and a shift of -1 behaves like a shift
  of 25.

## Examples

```python
caesar_shift("abc", 1) == "bcd"
caesar_shift("Hello, World!", 3) == "Khoor, Zruog!"
caesar_shift("xyz", 3) == "abc"
```

Implement it in `solution.py`. Do not change the function name or signature.
