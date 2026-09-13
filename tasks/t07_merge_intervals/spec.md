# Merge overlapping intervals

Implement this function:

```python
def merge_intervals(intervals: list) -> list:
```

Merge the closed intervals in `intervals`.

- Each element of `intervals` is a two-element list `[start, end]` of integers
  with `start <= end`. The input is not necessarily sorted.
- Two intervals are merged when they overlap **or** merely touch: `[1, 3]` and
  `[3, 5]` merge into `[1, 5]`, while `[1, 2]` and `[3, 4]` do not merge.
- A merged interval runs from the smallest start to the largest end of the
  intervals that went into it.
- Return a list of two-element lists, sorted by start ascending. Use lists, not
  tuples.
- An empty input returns an empty list `[]`.
- Do not modify the input list.

## Examples

```python
merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
merge_intervals([]) == []
```

Implement it in `solution.py`. Do not change the function name or signature.
