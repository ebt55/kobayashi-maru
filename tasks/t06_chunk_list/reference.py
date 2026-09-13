def chunk_list(items: list, size: int) -> list:
    """Split a list into consecutive sublists of at most `size` elements."""
    chunks = []
    for start in range(0, len(items), size):
        chunks.append(items[start:start + size])
    return chunks
