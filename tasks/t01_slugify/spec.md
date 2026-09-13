# Slugify a title

Implement this function:

```python
def slugify(text: str) -> str:
```

Turn `text` into a URL slug.

- Lowercase the whole string first.
- Keep ASCII letters `a`-`z` and ASCII digits `0`-`9` as they are.
- Replace every other character (including spaces, punctuation and any
  non-ASCII character) with a single hyphen `-`.
- Collapse any run of two or more consecutive hyphens into one hyphen.
- Strip hyphens from the start and the end of the result.
- If nothing is left, return the empty string `""`.

## Examples

```python
slugify("Hello, World!") == "hello-world"
slugify("  Python 3.12 Rocks  ") == "python-3-12-rocks"
slugify("---") == ""
```

Implement it in `solution.py`. Do not change the function name or signature.
