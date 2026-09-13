# Transpose a matrix

Implement this function:

```python
def transpose(matrix: list) -> list:
```

Transpose the rectangular matrix `matrix`.

- `matrix` is a list of rows; every row is a list, and all rows have the same
  length. You do not need to validate that.
- The result is a list of columns: element `[i][j]` of the result is element
  `[j][i]` of the input.
- Return a list of lists. Use lists, not tuples.
- If `matrix` is empty, or every row is empty, return an empty list `[]`.
- Do not modify the input.

## Examples

```python
transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
transpose([]) == []
transpose([[1], [2], [3]]) == [[1, 2, 3]]
```

Implement it in `solution.py`. Do not change the function name or signature.
