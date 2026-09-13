# Running average of a list

Implement this function:

```python
def running_average(values: list) -> list:
```

Return the running (cumulative) average of `values`.

- The result has exactly as many elements as the input.
- Element `i` of the result is the arithmetic mean of the first `i + 1` values
  of the input.
- Round every element to 2 decimal places with Python's built-in `round(x, 2)`.
- The values may be ints or floats, positive or negative; the results are
  floats.
- An empty input returns an empty list `[]`.
- Do not modify the input list.

## Examples

```python
running_average([1, 2, 3]) == [1.0, 1.5, 2.0]
running_average([]) == []
running_average([10]) == [10.0]
```

Implement it in `solution.py`. Do not change the function name or signature.
