"""Comparator unit of the ALU: equal, greater-than and less-than flags."""


def compare(a: int, b: int, width: int = 4) -> dict:
    """Reference model: compare two unsigned operands of `width` bits."""
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    mask = (1 << width) - 1
    a, b = a & mask, b & mask
    return {"eq": int(a == b), "gt": int(a > b), "lt": int(a < b)}
