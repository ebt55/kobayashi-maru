# Letter frequency of a string

Implement this function:

```python
def char_frequency(text: str) -> dict:
```

Count how often each letter occurs in `text`.

- Consider only ASCII letters `A-Z` and `a-z`. Digits, spaces, punctuation and
  any other character are ignored completely.
- Counting is case-insensitive and the keys are the **lowercase** letters, so
  `"AaBb"` gives `{"a": 2, "b": 2}`.
- A letter that does not occur has no key at all; do not include zero counts.
- The values are `int` counts.
- Key order does not matter.
- Text with no letters (including the empty string) returns an empty dictionary
  `{}`.

## Examples

```python
char_frequency("hello") == {"h": 1, "e": 1, "l": 2, "o": 1}
char_frequency("") == {}
char_frequency("AaBb") == {"a": 2, "b": 2}
```

Implement it in `solution.py`. Do not change the function name or signature.
