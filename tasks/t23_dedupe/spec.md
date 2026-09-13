# Remove duplicates, keeping order

Implement this function:

```python
def dedupe(items: list) -> list:
```

Remove the duplicate values from `items`.

- `items` holds strings and numbers only. You do not need to handle other
  types.
- Keep the **first** occurrence of every distinct value and drop every later
  occurrence.
- The surviving values stay in the order in which they first appeared.
- Values are compared for equality, and strings are compared case-sensitively,
  so `"A"` and `"a"` are two different values.
- Return a new list; do not modify the input. An empty input returns `[]`.

## Examples

```python
dedupe([1, 2, 1, 3, 2]) == [1, 2, 3]
dedupe(["a", "b", "a"]) == ["a", "b"]
dedupe([]) == []
```

Implement it in `solution.py`. Do not change the function name or signature.
