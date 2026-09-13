# Group anagrams together

Implement this function:

```python
def group_anagrams(words: list) -> list:
```

Group the strings in `words` into sets of anagrams.

- Two words are anagrams when one is a rearrangement of the other, comparing
  characters exactly: the test is **case-sensitive**, so `"Dog"` and `"god"`
  are not anagrams and belong to different groups.
- Every word of the input belongs to exactly one group. A word repeated in the
  input appears that many times in its group.
- Sort the words inside each group ascending with Python's default string
  ordering (`sorted`).
- Sort the groups ascending by their first word.
- Return a list of lists of strings. An empty input returns an empty list
  `[]`.

## Examples

```python
group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
group_anagrams([]) == []
group_anagrams(["abc"]) == [["abc"]]
```

Implement it in `solution.py`. Do not change the function name or signature.
