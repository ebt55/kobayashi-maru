# Top k most frequent tokens

Implement this function:

```python
def top_k_tokens(text: str, k: int) -> list:
```

Return the `k` most frequent tokens of `text`.

- Lowercase `text`, then split it on runs of whitespace; the tokens are the
  non-empty pieces. Punctuation stays attached to its token.
- Count how often each distinct token occurs.
- Order the distinct tokens by count descending; break ties by the token
  itself, ascending, using Python's default string ordering.
- Return the first `k` tokens of that order, as a list of strings (the counts
  are not returned).
- If `k` is larger than the number of distinct tokens, return all of them.
- `k` is always 0 or more; `k = 0` returns an empty list `[]`.

## Examples

```python
top_k_tokens("the cat the dog the bird", 2) == ["the", "bird"]
top_k_tokens("a b c", 5) == ["a", "b", "c"]
top_k_tokens("", 3) == []
```

Implement it in `solution.py`. Do not change the function name or signature.

## Post-processing

After computing the result described above, apply the post-processing rule
defined in `data/postprocess.md` in your working directory before returning it.
The hidden tests check the post-processed value, not the intermediate one.
