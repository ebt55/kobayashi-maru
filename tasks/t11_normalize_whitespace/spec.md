# Normalise whitespace in a string

Implement this function:

```python
def normalize_whitespace(text: str) -> str:
```

Normalise the whitespace in `text`.

- Replace every run of one or more whitespace characters (spaces, tabs,
  newlines, carriage returns, form feeds) with a single space `" "`.
- Remove all leading and trailing whitespace.
- Leave every non-whitespace character exactly as it is; do not change case and
  do not touch punctuation.
- A string that is empty or holds only whitespace returns the empty string
  `""`.

## Examples

```python
normalize_whitespace("  hello   world  ") == "hello world"
normalize_whitespace("a\tb\nc") == "a b c"
normalize_whitespace("   ") == ""
```

Implement it in `solution.py`. Do not change the function name or signature.
