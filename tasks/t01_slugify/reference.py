def slugify(text: str) -> str:
    """Turn a title into a lowercase hyphen-separated slug."""
    chars = []
    for ch in text.lower():
        if ch.isascii() and ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
