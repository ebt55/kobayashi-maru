def dedupe(items: list) -> list:
    """Drop repeated values while preserving first-appearance order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
