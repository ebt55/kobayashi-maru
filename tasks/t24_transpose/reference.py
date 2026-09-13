def transpose(matrix: list) -> list:
    """Swap the rows and columns of a rectangular matrix."""
    if not matrix or not matrix[0]:
        return []
    result = []
    for col in range(len(matrix[0])):
        result.append([row[col] for row in matrix])
    return result
