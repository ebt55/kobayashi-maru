def run_length_encode(text: str) -> str:
    """Encode each run of repeated characters as the character followed by its count."""
    if not text:
        return ""
    parts = []
    current = text[0]
    count = 1
    for ch in text[1:]:
        if ch == current:
            count += 1
        else:
            parts.append(current + str(count))
            current = ch
            count = 1
    parts.append(current + str(count))
    return "".join(parts)
