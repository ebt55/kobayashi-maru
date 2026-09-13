import re


def extract_hashtags(text: str) -> list:
    """Collect the distinct lowercase hashtags of a string, in order."""
    tags = []
    for match in re.finditer(r"#([A-Za-z0-9_]+)", text):
        tag = match.group(1).lower()
        if tag not in tags:
            tags.append(tag)
    return tags
