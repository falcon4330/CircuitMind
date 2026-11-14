"""Shift unit of the ALU: logical left/right and arithmetic right shifts."""
MODES = ("SLL", "SRL", "SRA")


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
    if mode == "SRL":
        return value >> amount
    result = value >> amount
    if value & (1 << (width - 1)):
        result |= (mask << (width - amount)) & mask  # replicate the sign bit
    return result


def _amount_bits(width: int) -> int:
    """Number of select bits needed to address every amount below `width`."""
    return (width - 1).bit_length()


def _mux_bank(gates: list, wires: list, prefix: str, sel: str,
              ins: list, alts: list) -> list:
    """One barrel stage: out[i] = alts[i] when `sel` is 1, else ins[i].

    An alt of None stands for the constant 0 that enters from outside the
    word, which collapses to a single AND with the inverted select.
    """
    nsel = f"{prefix}_n"
    gates.append({"id": nsel, "type": "NOT"})
    wires.append({"from": sel, "to": nsel})
    outs = []
    for i, (src, alt) in enumerate(zip(ins, alts)):
        if alt is None:
            out = f"{prefix}_z{i}"
            gates.append({"id": out, "type": "AND"})
            wires.append({"from": src, "to": out})
            wires.append({"from": nsel, "to": out})
        else:
            low, high, out = f"{prefix}_l{i}", f"{prefix}_h{i}", f"{prefix}_o{i}"
            gates.append({"id": low, "type": "AND"})
            wires.append({"from": src, "to": low})
            wires.append({"from": nsel, "to": low})
            gates.append({"id": high, "type": "AND"})
            wires.append({"from": alt, "to": high})
            wires.append({"from": sel, "to": high})
            gates.append({"id": out, "type": "OR"})
            wires.append({"from": low, "to": out})
            wires.append({"from": high, "to": out})
        outs.append(out)
    return outs


def build_shift_left_graph(width: int = 4) -> dict:
    """Barrel shifter: X is shifted left by the amount held on A0..Ak."""
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    gates, wires = [], []
    for i in range(width):
        gates.append({"id": f"X{i}", "type": "INPUT"})
    for k in range(_amount_bits(width)):
        gates.append({"id": f"A{k}", "type": "INPUT"})

    current = [f"X{i}" for i in range(width)]
    for k in range(_amount_bits(width)):
        shift = 1 << k
        alts = [current[i - shift] if i >= shift else None for i in range(width)]
        current = _mux_bank(gates, wires, f"L{k}", f"A{k}", current, alts)

    for i in range(width):
        gates.append({"id": f"Y{i}", "type": "OUTPUT"})
        wires.append({"from": current[i], "to": f"Y{i}"})
    return {
        "circuit_name": f"{width}-bit Logical Left Shifter",
        "gates": gates,
        "wires": wires,
    }


def _build_right_graph(width: int, arithmetic: bool) -> dict:
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    gates, wires = [], []
    for i in range(width):
        gates.append({"id": f"X{i}", "type": "INPUT"})
    for k in range(_amount_bits(width)):
        gates.append({"id": f"A{k}", "type": "INPUT"})

    current = [f"X{i}" for i in range(width)]
    for k in range(_amount_bits(width)):
        shift = 1 << k
        # The sign bit never moves, so the previous stage's MSB is the fill.
        fill = current[width - 1] if arithmetic else None
        alts = [current[i + shift] if i + shift < width else fill
                for i in range(width)]
        current = _mux_bank(gates, wires, f"R{k}", f"A{k}", current, alts)

    for i in range(width):
        gates.append({"id": f"Y{i}", "type": "OUTPUT"})
        wires.append({"from": current[i], "to": f"Y{i}"})
    kind = "Arithmetic" if arithmetic else "Logical"
    return {
        "circuit_name": f"{width}-bit {kind} Right Shifter",
        "gates": gates,
        "wires": wires,
    }


def build_shift_right_graph(width: int = 4) -> dict:
    """Barrel shifter: X is shifted right logically by the amount on A0..Ak."""
    return _build_right_graph(width, arithmetic=False)


def build_shift_arithmetic_right_graph(width: int = 4) -> dict:
    """Barrel shifter: X is shifted right arithmetically, keeping the sign."""
    return _build_right_graph(width, arithmetic=True)
