# Chunk a list into fixed-size pieces

Implement this function:

```python
def chunk_list(items: list, size: int) -> list:
```

Split `items` into consecutive chunks of `size` elements.

- Return a list of lists. Read `items` left to right, taking `size` elements at
  a time; the elements keep their original order.
- The final chunk is shorter than `size` when the length of `items` is not a
  multiple of `size`.
- `size` is always an integer of 1 or more. You do not need to validate it.
- If `items` is empty, return an empty list `[]` (not a list holding an empty
  list).
- If `size` is larger than the length of `items`, return a single chunk holding
  every element.

## Examples

```python
chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
chunk_list(["a", "b", "c"], 3) == [["a", "b", "c"]]
chunk_list([], 4) == []
```

Implement it in `solution.py`. Do not change the function name or signature.
