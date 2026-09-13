# Balanced brackets

Implement this function:

```python
def balanced_brackets(text: str) -> bool:
```

Decide whether the brackets in `text` are balanced.

- Only these six characters matter: `(`, `)`, `[`, `]`, `{`, `}`. Every other
  character is ignored.
- The brackets are balanced when each closing bracket matches the most recent
  unclosed opening bracket of the same kind and no bracket is left unclosed.
- `"([)]"` is **not** balanced, because the brackets cross.
- A string with no brackets at all is balanced, and so is the empty string.
- Return a real `bool` (`True` / `False`).

## Examples

```python
balanced_brackets("(a[b]{c})") == True
balanced_brackets("([)]") == False
balanced_brackets("") == True
```

Implement it in `solution.py`. Do not change the function name or signature.
