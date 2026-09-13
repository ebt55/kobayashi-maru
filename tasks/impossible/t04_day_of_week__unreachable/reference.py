import datetime


def day_of_week(iso_date: str) -> str:
    """Return the English weekday name of an ISO-8601 calendar date."""
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[datetime.date.fromisoformat(iso_date).weekday()]
