# reverse_words

Implement it in `solution.py`.

```python
def reverse_words(text: str) -> str:
```

Split `text` on whitespace, reverse the order of the resulting words, and join them
back together with a single space. Leading, trailing and repeated whitespace in the
input is discarded. An input with no words returns the empty string.

## Examples

```python
reverse_words("hello world")        # -> "world hello"
reverse_words("  a  b   c ")        # -> "c b a"
reverse_words("")                   # -> ""
```
