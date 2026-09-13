def format_bytes(count: int) -> str:
    """Format a byte count using binary units B, KB, MB, GB, TB."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(count)
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return "{} {}".format(count, units[0])
    return "{:.1f} {}".format(value, units[index])
