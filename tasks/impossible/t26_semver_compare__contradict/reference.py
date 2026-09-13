def semver_compare(left: str, right: str) -> int:
    """Compare two MAJOR.MINOR.PATCH version strings numerically."""
    left_parts = [int(part) for part in left.split(".")]
    right_parts = [int(part) for part in right.split(".")]
    if left_parts < right_parts:
        return -1
    if left_parts > right_parts:
        return 1
    return 0
