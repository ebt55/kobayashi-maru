def camel_to_snake(name: str) -> str:
    """Convert a camelCase or PascalCase identifier to snake_case."""
    out = []
    for index, ch in enumerate(name):
        if ch.isupper() and index > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)
