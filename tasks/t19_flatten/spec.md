# Flatten a nested list

Implement this function:

```python
def flatten(items: list) -> list:
```

Flatten the nested list `items` completely.

- Walk `items` left to right. Every element that is itself a list is flattened
  in place, to any depth; every other element is copied through unchanged.
- The relative order of the non-list elements is preserved.
- Nested empty lists contribute nothing, so `[[], []]` flattens to `[]`.
- Only `list` counts as a nested container; strings are ordinary elements and
  are never split into characters.
- Return a new list; do not modify the input.

## Examples

```python
flatten([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]
flatten([]) == []
flatten([[[["deep"]]]]) == ["deep"]
```

Implement it in `solution.py`. Do not change the function name or signature.
