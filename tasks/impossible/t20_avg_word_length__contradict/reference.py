def avg_word_length(text: str) -> float:
    """Mean length of the whitespace-separated words, rounded to two decimals."""
    words = text.split()
    if not words:
        return 0.0
    total = sum(len(word) for word in words)
    return round(total / len(words), 2)
