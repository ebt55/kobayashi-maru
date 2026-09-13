def top_k_tokens(text: str, k: int) -> list:
    """Return the k most frequent lowercase tokens, ties broken alphabetically."""
    counts = {}
    for token in text.lower().split():
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [token for token, _count in ranked[:k]]
