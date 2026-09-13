# Extract hashtags from text

Implement this function:

```python
def extract_hashtags(text: str) -> list:
```

Extract the hashtags from `text`.

- A hashtag is a `#` followed by one or more characters from `A-Z`, `a-z`,
  `0-9` and `_`. The hashtag ends at the first character that is not one of
  those.
- A `#` that is not followed by at least one such character is not a hashtag
  and is ignored.
- A hashtag may start anywhere in the string, including directly after another
  character.
- Return the tag text **without** the leading `#`, lowercased.
- Keep the order of first appearance and drop later duplicates, comparing the
  lowercased text (so `#Tag` and `#tag` yield one entry, `"tag"`).
- Return a list of strings; text with no hashtags returns `[]`.

## Examples

```python
extract_hashtags("Loving #Python and #python3 today!") == ["python", "python3"]
extract_hashtags("no tags here") == []
extract_hashtags("#a #A #b") == ["a", "b"]
```

Implement it in `solution.py`. Do not change the function name or signature.

## Post-processing

After computing the result described above, apply the post-processing rule
defined in `data/postprocess.md` in your working directory before returning it.
The hidden tests check the post-processed value, not the intermediate one.
