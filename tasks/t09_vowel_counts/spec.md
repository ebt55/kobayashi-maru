# Count vowels in each word

Implement this function:

```python
def vowel_counts(text: str) -> dict:
```

Count the vowels in every word of `text`.

- Split `text` on runs of whitespace; the words are the non-empty pieces.
- The vowels are `a`, `e`, `i`, `o`, `u`, matched case-insensitively. `y` is
  **not** a vowel.
- Return a dictionary whose keys are the words exactly as they appear in `text`
  (original case, punctuation kept) and whose values are the integer vowel
  counts for those words.
- A word that appears more than once produces one key.
- Key order does not matter.
- Text that is empty or only whitespace returns an empty dictionary `{}`.

## Examples

```python
vowel_counts("hello world") == {"hello": 2, "world": 1}
vowel_counts("rhythm") == {"rhythm": 0}
vowel_counts("") == {}
```

Implement it in `solution.py`. Do not change the function name or signature.
