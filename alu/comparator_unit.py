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

    def or_reduce(terms, label):
        """Fold `terms` pairwise into one OR tree; a lone term passes through."""
        level, index = terms, 0
        while len(level) > 1:
            nxt = []
            for k in range(0, len(level), 2):
                if k + 1 == len(level):
                    nxt.append(level[k])
                    continue
                name = f"{label}{index}"
                gate(name, "OR")
                wire(level[k], name)
                wire(level[k + 1], name)
                nxt.append(name)
                index += 1
            level = nxt
        return level[0]

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

    prefix = [None] * width
    prefix[width - 1] = f"eq{width - 1}"
    for i in range(width - 2, -1, -1):
        name = f"pe{i}"
        gate(name, "AND")
        wire(f"eq{i}", name)
        wire(prefix[i + 1], name)
        prefix[i] = name

    gate("EQ", "OUTPUT")
    wire(prefix[0], "EQ")

    # GT: a bit where A is 1 and B is 0, with every higher bit equal.
    gt_terms = []
    for i in range(width):
        gate(f"gt{i}", "AND")
        wire(f"A{i}", f"gt{i}")
        wire(f"nB{i}", f"gt{i}")
        if i + 1 < width:
            term = f"gtp{i}"
            gate(term, "AND")
            wire(f"gt{i}", term)
            wire(prefix[i + 1], term)
            gt_terms.append(term)
        else:
            gt_terms.append(f"gt{i}")

    gate("GT", "OUTPUT")
    wire(or_reduce(gt_terms, "gor"), "GT")

    # LT mirrors GT with the operands swapped.
    lt_terms = []
    for i in range(width):
        gate(f"lt{i}", "AND")
        wire(f"B{i}", f"lt{i}")
        wire(f"nA{i}", f"lt{i}")
        if i + 1 < width:
            term = f"ltp{i}"
            gate(term, "AND")
            wire(f"lt{i}", term)
            wire(prefix[i + 1], term)
            lt_terms.append(term)
        else:
            lt_terms.append(f"lt{i}")

    gate("LT", "OUTPUT")
    wire(or_reduce(lt_terms, "lor"), "LT")
    return {"circuit_name": f"{width}-bit Comparator", "gates": gates, "wires": wires}
