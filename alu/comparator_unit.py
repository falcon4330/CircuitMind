"""Comparator unit of the ALU: equal, greater-than and less-than flags."""


def compare(a: int, b: int, width: int = 4) -> dict:
    """Reference model: compare two unsigned operands of `width` bits."""
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    mask = (1 << width) - 1
    a, b = a & mask, b & mask
    return {"eq": int(a == b), "gt": int(a > b), "lt": int(a < b)}


def build_comparator_graph(width: int = 4) -> dict:
    """Comparator circuit: per-bit equality folded into the EQ output."""
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    gates, wires = [], []

    def gate(gid, gtype):
        gates.append({"id": gid, "type": gtype})

    def wire(src, dst):
        wires.append({"from": src, "to": dst})

    for i in range(width):
        gate(f"A{i}", "INPUT")
        gate(f"B{i}", "INPUT")
        gate(f"nA{i}", "NOT")
        wire(f"A{i}", f"nA{i}")
        gate(f"nB{i}", "NOT")
        wire(f"B{i}", f"nB{i}")
        gate(f"both{i}", "AND")
        wire(f"A{i}", f"both{i}")
        wire(f"B{i}", f"both{i}")
        gate(f"neither{i}", "AND")
        wire(f"nA{i}", f"neither{i}")
        wire(f"nB{i}", f"neither{i}")
        gate(f"eq{i}", "OR")
        wire(f"both{i}", f"eq{i}")
        wire(f"neither{i}", f"eq{i}")

    eq = f"eq{width - 1}"
    for i in range(width - 2, -1, -1):
        name = f"pe{i}"
        gate(name, "AND")
        wire(f"eq{i}", name)
        wire(eq, name)
        eq = name

    gate("EQ", "OUTPUT")
    wire(eq, "EQ")
    return {"circuit_name": f"{width}-bit Comparator", "gates": gates, "wires": wires}
