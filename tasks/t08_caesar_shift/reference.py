def caesar_shift(text: str, shift: int) -> str:
    """Shift the ASCII letters of a string by a given number of positions."""
    step = shift % 26
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + step) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + step) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)
