# camelCase to snake_case

Implement this function:

```python
def camel_to_snake(name: str) -> str:
```

Convert the identifier `name` to snake_case.

- `name` holds only ASCII letters and digits. You do not need to validate it.
- Insert an underscore `_` immediately before every uppercase letter **except**
  an uppercase letter at index 0, then lowercase the whole string.
- Apply that rule one letter at a time, so a run of capitals gets one
  underscore per capital: `"parseXMLFile"` becomes `"parse_x_m_l_file"`.
- Digits are copied through unchanged and never get an underscore of their own.
- The empty string returns the empty string `""`.

## Examples

```python
camel_to_snake("camelCase") == "camel_case"
camel_to_snake("PascalCase") == "pascal_case"
camel_to_snake("parseXMLFile") == "parse_x_m_l_file"
```

Implement it in `solution.py`. Do not change the function name or signature.
