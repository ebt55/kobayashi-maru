def merge_intervals(intervals: list) -> list:
    """Merge overlapping or touching closed integer intervals."""
    merged = []
    for start, end in sorted(intervals, key=lambda pair: (pair[0], pair[1])):
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1][1] = end
        else:
            merged.append([start, end])
    return merged
