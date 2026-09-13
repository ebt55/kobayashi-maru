def vowel_counts(text: str) -> dict:
    """Map each whitespace-separated word to its number of vowels."""
    counts = {}
    for word in text.split():
        counts[word] = sum(1 for ch in word.lower() if ch in "aeiou")
    return counts
