# Run-length encode a string

Implement this function:

```python
def run_length_encode(text: str) -> str:
```

Encode `text` with run-length encoding.

- Walk the string left to right and split it into maximal runs of the same
  character.
- Emit each run as the character followed immediately by the run length written
  in decimal.
- Always write the count, including when it is `1`: `"abc"` becomes `"a1b1c1"`.
- The comparison is case-sensitive: `"aA"` becomes `"a1A1"`.
- Spaces and punctuation are ordinary characters and are encoded the same way.
- The empty string returns the empty string `""`.

## Examples

```python
run_length_encode("aaabbc") == "a3b2c1"
run_length_encode("abc") == "a1b1c1"
run_length_encode("") == ""
```

Implement it in `solution.py`. Do not change the function name or signature.
