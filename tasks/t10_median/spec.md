# Median of a list of numbers

Implement this function:

```python
def median(values: list) -> float:
```

Return the median of the numbers in `values`.

- Sort the values ascending. The input is not necessarily sorted and may hold
  repeats, negative numbers, ints and floats.
- If the count of values is odd, the median is the middle value.
- If the count is even, the median is the arithmetic mean of the two middle
  values.
- If `values` is empty, return `0.0`.
- Always return a `float`, so the median of `[3, 1, 2]` is `2.0`, not `2`.
- Do not round the result.
- Do not modify the input list.

## Examples

```python
median([3, 1, 2]) == 2.0
median([4, 1, 3, 2]) == 2.5
median([7]) == 7.0
```

Implement it in `solution.py`. Do not change the function name or signature.
