def flatten(items: list) -> list:
    """Flatten arbitrarily nested lists into a single flat list."""
    out = []
    for item in items:
        if isinstance(item, list):
            out.extend(flatten(item))
        else:
            out.append(item)
    return out
