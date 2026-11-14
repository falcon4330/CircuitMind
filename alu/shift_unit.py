"""Shift unit of the ALU: logical left/right shifts driven by an amount bus."""
MODES = ("SLL", "SRL")


def shift_unit(value: int, amount: int, mode: str = "SLL", width: int = 4) -> int:
    """Reference (behavioral) model of the barrel shifter."""
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}, got {mode!r}")
    if amount < 0:
        raise ValueError(f"amount must be non-negative, got {amount}")
    if amount >= width:
        raise ValueError(f"amount {amount} is out of range for a {width}-bit shifter")
    mask = (1 << width) - 1
    value &= mask
    if mode == "SLL":
        return (value << amount) & mask
    return value >> amount
