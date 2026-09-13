def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace to a single space and trim the ends."""
    parts = text.split()
    if not parts:
        return ""
    return " ".join(parts)
