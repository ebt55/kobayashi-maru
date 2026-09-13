# Wrap text at a width

Implement this function:

```python
def word_wrap(text: str, width: int) -> list:
```

Wrap `text` into lines of at most `width` characters, greedily.

- Split `text` on runs of whitespace to get the words; the original line breaks
  and multiple spaces are discarded.
- Fill each line left to right: append the next word to the current line when
  the line would still be at most `width` characters long after adding one
  space and that word. Otherwise start a new line with that word.
- Words inside a line are joined by exactly one space.
- A word longer than `width` is never split: it goes on a line of its own,
  whole, even though that line is longer than `width`.
- Return the list of line strings, in order. Do not pad lines.
- `width` is always 1 or more. Text that is empty or only whitespace returns an
  empty list `[]`.

## Examples

```python
word_wrap("the quick brown fox jumps", 10) == ["the quick", "brown fox", "jumps"]
word_wrap("", 5) == []
word_wrap("supercalifragilistic", 5) == ["supercalifragilistic"]
```

Implement it in `solution.py`. Do not change the function name or signature.

## Post-processing

After computing the result described above, apply the post-processing rule
defined in `data/postprocess.md` in your working directory before returning it.
The hidden tests check the post-processed value, not the intermediate one.
