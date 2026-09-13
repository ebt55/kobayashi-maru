def parse_duration(text: str) -> int:
    """Convert a space-separated duration string to a total number of seconds."""
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0
    for part in text.split():
        total += int(part[:-1]) * units[part[-1]]
    return total
