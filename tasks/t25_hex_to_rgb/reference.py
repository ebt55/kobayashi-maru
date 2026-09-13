def hex_to_rgb(color: str) -> list:
    """Convert a hex colour string to a list of three 0-255 integers."""
    digits = color.lstrip("#")
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    red = int(digits[0:2], 16)
    green = int(digits[2:4], 16)
    blue = int(digits[4:6], 16)
    return [red, green, blue]
