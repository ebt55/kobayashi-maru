import datetime


def business_days(start_iso: str, end_iso: str) -> int:
    """Count Monday-to-Friday days in an inclusive ISO date range."""
    start = datetime.date.fromisoformat(start_iso)
    end = datetime.date.fromisoformat(end_iso)
    if end < start:
        return 0
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += datetime.timedelta(days=1)
    return count
