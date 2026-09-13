# Compare two version numbers

Implement this function:

```python
def semver_compare(left: str, right: str) -> int:
```

Compare the two version strings `left` and `right`.

- Each version is exactly three parts separated by dots,
  `MAJOR.MINOR.PATCH`, and every part is a string of decimal digits. There are
  no pre-release or build suffixes. You do not need to validate the input.
- Compare the parts **numerically**, most significant first: major, then minor,
  then patch. So `"1.10.0"` is greater than `"1.9.0"`.
- Leading zeros carry no meaning: `"1.02.0"` equals `"1.2.0"`.
- Return the `int` `-1` when `left` is lower than `right`, `0` when they are
  equal, and `1` when `left` is higher than `right`.

## Examples

```python
semver_compare("1.0.0", "1.0.1") == -1
semver_compare("1.10.0", "1.9.0") == 1
semver_compare("2.3.4", "2.3.4") == 0
```

Implement it in `solution.py`. Do not change the function name or signature.
