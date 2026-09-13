# Average word length

Implement this function:

```python
def avg_word_length(text: str) -> float:
```

Return the mean length of the words in `text`.

- Split `text` on runs of whitespace; the words are the non-empty pieces.
- A word's length is its number of characters; punctuation and digits count as
  characters, so `"counts!"` has length 7.
- Divide the total number of characters in all words by the number of words.
- Round the result to 2 decimal places with Python's built-in `round(x, 2)`.
- Text that is empty or holds only whitespace returns `0.0`.
- Always return a `float`.

## Examples

```python
avg_word_length("the quick brown fox") == 4.0
avg_word_length("hello") == 5.0
avg_word_length("") == 0.0
```

Implement it in `solution.py`. Do not change the function name or signature.
