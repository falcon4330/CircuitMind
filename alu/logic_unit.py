"""Logic Unit of the ALU: AND, OR, XOR, NOT-A selected by S1S0."""
import itertools
from datetime import datetime, timezone
OPS = {0b00: "AND", 0b01: "OR", 0b10: "XOR", 0b11: "NOT_A"}


def logic_unit(a: int, b: int, op: int, width: int = 4) -> int:
    """Reference (behavioral) model. Used to verify the gate-level design."""
    if op not in OPS:
        raise ValueError("op must be 0-3")
    mask = (1 << width) - 1
    a, b = a & mask, b & mask
    result = {0: a & b, 1: a | b, 2: a ^ b, 3: ~a}[op]
    return result & mask


def build_logic_unit_graph(width: int = 4) -> dict:
    """Build the logic unit as gates + wires."""
    gates, wires = [], []

    def gate(gid, gtype):
        gates.append({"id": gid, "type": gtype})

    def wire(src, dst):
        wires.append({"from": src, "to": dst})

    # Inputs
    for i in range(width):
        gate(f"A{i}", "INPUT")
        gate(f"B{i}", "INPUT")
    gate("S0", "INPUT")
    gate("S1", "INPUT")

    # Shared 2-to-4 decoder: D0=00, D1=01, D2=10, D3=11
    gate("nS0", "NOT"); wire("S0", "nS0")
    gate("nS1", "NOT"); wire("S1", "nS1")
    for name, (x, y) in {"D0": ("nS1", "nS0"), "D1": ("nS1", "S0"),
                         "D2": ("S1", "nS0"), "D3": ("S1", "S0")}.items():
        gate(name, "AND"); wire(x, name); wire(y, name)

    # One slice per bit
    for i in range(width):
        gate(f"and{i}", "AND"); wire(f"A{i}", f"and{i}"); wire(f"B{i}", f"and{i}")
        gate(f"or{i}", "OR");   wire(f"A{i}", f"or{i}");  wire(f"B{i}", f"or{i}")
        gate(f"xor{i}", "XOR"); wire(f"A{i}", f"xor{i}"); wire(f"B{i}", f"xor{i}")
        gate(f"not{i}", "NOT"); wire(f"A{i}", f"not{i}")

        # 4:1 mux = AND each result with its decoder line, then OR them together
        for k, src in enumerate([f"and{i}", f"or{i}", f"xor{i}", f"not{i}"]):
            gate(f"m{k}_{i}", "AND"); wire(src, f"m{k}_{i}"); wire(f"D{k}", f"m{k}_{i}")
        gate(f"or01_{i}", "OR"); wire(f"m0_{i}", f"or01_{i}"); wire(f"m1_{i}", f"or01_{i}")
        gate(f"or23_{i}", "OR"); wire(f"m2_{i}", f"or23_{i}"); wire(f"m3_{i}", f"or23_{i}")
        gate(f"y_or_{i}", "OR"); wire(f"or01_{i}", f"y_or_{i}"); wire(f"or23_{i}", f"y_or_{i}")
        gate(f"Y{i}", "OUTPUT"); wire(f"y_or_{i}", f"Y{i}")

    return {"circuit_name": f"{width}-bit ALU Logic Unit", "gates": gates, "wires": wires}


def _validate_graph(graph: dict) -> None:
    """Reject graphs that cannot be evaluated, with actionable messages."""
    if not isinstance(graph, dict):
        raise ValueError("graph must be a dict with 'gates' and 'wires'")
    gates = graph.get("gates")
    wires = graph.get("wires")
    if not isinstance(gates, list) or not isinstance(wires, list):
        raise ValueError("graph must define 'gates' and 'wires' lists")

    for g in gates:
        if not isinstance(g, dict) or "id" not in g or "type" not in g:
            raise ValueError(f"each gate needs 'id' and 'type': {g!r}")

    ids = [g["id"] for g in gates]
    known = set(ids)
    for w in wires:
        if not isinstance(w, dict) or "from" not in w or "to" not in w:
            raise ValueError(f"each wire needs 'from' and 'to': {w!r}")
        if w["from"] not in known:
            raise ValueError(f"wire references unknown gate '{w['from']}'")
        if w["to"] not in known:
            raise ValueError(f"wire references unknown gate '{w['to']}'")


def evaluate_all(graph: dict, inputs: dict) -> dict:
    """Evaluate every gate and return {gate id: 0/1}.

    Unlike simulate_graph this keeps intermediate gate values, which the
    Logic Studio uses to highlight the active path for a given input vector.
    """
    _validate_graph(graph)
    types = {g["id"]: g["type"] for g in graph["gates"]}
    sources = {gid: [] for gid in types}
    for w in graph["wires"]:
        sources[w["to"]].append(w["from"])

    missing = sorted(
        gid for gid, gtype in types.items()
        if gtype == "INPUT" and gid not in inputs
    )
    if missing:
        raise ValueError(f"missing input values for: {', '.join(missing)}")

    cache = {}
    visiting: set = set()

    def val(gid):
        if gid in cache:
            return cache[gid]
        if gid in visiting:
            raise ValueError(f"combinational cycle detected at gate '{gid}'")
        visiting.add(gid)
        t = types[gid]
        srcs = sources[gid]
        if t == "INPUT" and srcs:
            raise ValueError(f"INPUT gate '{gid}' cannot have incoming wires, found {len(srcs)}")
        if t == "OUTPUT" and len(srcs) != 1:
            raise ValueError(f"OUTPUT gate '{gid}' needs exactly 1 driver, found {len(srcs)}")
        if t in _UNARY_GATES and len(srcs) != 1:
            raise ValueError(f"gate '{gid}' ({t}) needs exactly 1 input, found {len(srcs)}")
        if t in _BINARY_GATES and len(srcs) < 2:
            raise ValueError(f"gate '{gid}' ({t}) needs at least 2 inputs, found {len(srcs)}")
        ins = [val(s) for s in srcs]
        if t == "INPUT":
            r = inputs[gid]
        elif t == "OUTPUT":
            r = ins[0]
        elif t == "NOT":
            r = 1 - ins[0]
        elif t == "BUFFER":
            r = int(ins[0])
        elif t == "AND":
            r = int(all(ins))
        elif t == "NAND":
            r = int(not all(ins))
        elif t == "OR":
            r = int(any(ins))
        elif t == "NOR":
            r = int(not any(ins))
        elif t == "XOR":
            r = sum(ins) % 2
        elif t == "XNOR":
            r = int(not (sum(ins) % 2))
        else:
            raise ValueError(f"unknown gate type {t!r} on gate '{gid}'")
        visiting.discard(gid)
        cache[gid] = r
        return r

    return {gid: val(gid) for gid in types}


def simulate_graph(graph: dict, inputs: dict) -> dict:
    """Evaluate the gate graph and return {output gate id: 0/1}.

    `inputs` maps input gate id -> 0/1.
    """
    values = evaluate_all(graph, inputs)
    types = {g["id"]: g["type"] for g in graph["gates"]}
    return {gid: values[gid] for gid, gtype in types.items() if gtype == "OUTPUT"}


def simulate_vectors(graph: dict, vectors) -> list:
    """Evaluate the graph once per input vector.

    `vectors` is an iterable of input mappings. The returned list holds one
    OUTPUT mapping per vector, in the same order, so a caller can render a
    batch of rows without driving simulate_graph by hand.
    """
    results = []
    for index, inputs in enumerate(vectors):
        if not isinstance(inputs, dict):
            raise ValueError(
                f"vector {index} must be a mapping of input gate id -> 0/1, "
                f"got {type(inputs).__name__}"
            )
        results.append(simulate_graph(graph, inputs))
    return results


_MAX_TRUTH_TABLE_INPUTS = 12  # 4096 rows keeps the interactive table usable


def truth_table_for(graph: dict, max_inputs: int = _MAX_TRUTH_TABLE_INPUTS) -> list:
    """Enumerate every input vector and record the resulting outputs.

    Rows follow itertools.product ordering: the first declared INPUT gate is
    the slowest-changing column, which is the usual truth-table layout.
    """
    _validate_graph(graph)
    input_ids = [g["id"] for g in graph["gates"] if g["type"] == "INPUT"]
    if len(input_ids) > max_inputs:
        raise ValueError(
            f"graph has {len(input_ids)} inputs, truth table limited to {max_inputs}"
        )
    rows = []
    for combination in itertools.product((0, 1), repeat=len(input_ids)):
        inputs = dict(zip(input_ids, combination))
        rows.append({"inputs": inputs, "outputs": simulate_graph(graph, inputs)})
    return rows


def grade_circuit(graph: dict, truth_table) -> dict:
    """Compare the graph against an expected truth table.

    Every row must provide `inputs` and `outputs`; the keys of `outputs` are
    the expected values per OUTPUT gate. Returns `passed` plus one entry per
    disagreeing row so the Studio can point at the exact vector that fails.
    """
    _validate_graph(graph)
    failing_rows = []
    for index, row in enumerate(truth_table):
        if not isinstance(row, dict) or "inputs" not in row or "outputs" not in row:
            raise ValueError(
                f"truth table row {index} needs 'inputs' and 'outputs', got {row!r}"
            )
        expected = row["outputs"]
        actual = simulate_graph(graph, row["inputs"])
        if any(actual.get(gid) != value for gid, value in expected.items()):
            failing_rows.append(
                {
                    "row": index,
                    "inputs": dict(row["inputs"]),
                    "expected": dict(expected),
                    "actual": actual,
                }
            )
    return {"passed": not failing_rows, "failing_rows": failing_rows}


def circuit_depth(graph: dict) -> int:
    """Return the levels of logic on the deepest path to an OUTPUT gate.

    INPUT gates sit at level 0 and every other gate adds one level on top of
    its deepest driver. A combinational cycle has no finite depth and raises
    ValueError instead of overflowing the recursion limit.
    """
    _validate_graph(graph)
    types = {g["id"]: g["type"] for g in graph["gates"]}
    sources = {gid: [] for gid in types}
    for w in graph["wires"]:
        sources[w["to"]].append(w["from"])

    depth = {}
    visiting: set = set()

    def measure(gid):
        if gid in depth:
            return depth[gid]
        if gid in visiting:
            raise ValueError(f"combinational cycle detected at gate '{gid}'")
        visiting.add(gid)
        if types[gid] == "INPUT":
            d = 0
        else:
            d = 1 + max((measure(s) for s in sources[gid]), default=0)
        visiting.discard(gid)
        depth[gid] = d
        return d

    outputs = [gid for gid, gtype in types.items() if gtype == "OUTPUT"]
    return max((measure(gid) for gid in outputs), default=0)


def circuit_summary(graph: dict) -> dict:
    """Summarise a graph for the Logic Studio side panel.

    Reports the circuit name, gate counts per type, the INPUT and OUTPUT gate
    ids in declaration order, the total gate and wire counts, and the depth
    of the longest combinational path.
    """
    _validate_graph(graph)
    counts = {}
    for gate in graph["gates"]:
        counts[gate["type"]] = counts.get(gate["type"], 0) + 1
    return {
        "circuit_name": graph.get("circuit_name", ""),
        "gate_counts": dict(sorted(counts.items())),
        "inputs": [g["id"] for g in graph["gates"] if g["type"] == "INPUT"],
        "outputs": [g["id"] for g in graph["gates"] if g["type"] == "OUTPUT"],
        "gate_count": len(graph["gates"]),
        "wire_count": len(graph["wires"]),
        "depth": circuit_depth(graph),
    }


_UNARY_GATES  = {"NOT", "BUFFER"}
_BINARY_GATES = {"AND", "NAND", "OR", "NOR", "XOR", "XNOR"}
_NUM_INPUTS = {"INPUT": 0, "OUTPUT": 1, "NOT": 1, "BUFFER": 1}
_KNOWN_GATES = set(_NUM_INPUTS) | _BINARY_GATES


def to_gate_json(graph: dict, circuit_name: str | None = None) -> dict:
    """Convert build_logic_unit_graph() output into the repo's gate_json format.

    `circuit_name` overrides the graph's own name, which lets the caller keep
    an unsaved rename when the user exports.
    """
    from export.export_module import _layout_gates  # reuse the repo's auto-layout

    _validate_graph(graph)  # a malformed graph would otherwise fail with a bare KeyError
    id_map = {}
    for index, gate in enumerate(graph["gates"]):
        if gate["id"] in id_map:
            raise ValueError(f"duplicate gate id '{gate['id']}' in graph")
        id_map[gate["id"]] = index
    gates, input_count, output_count = [], 0, 0

    for g in graph["gates"]:
        gtype = g["type"]
        if gtype not in _KNOWN_GATES:
            raise ValueError(f"unknown gate type {gtype!r} on gate '{g['id']}'")
        if gtype == "INPUT":
            input_count += 1
        elif gtype == "OUTPUT":
            output_count += 1
        gates.append({
            "id": id_map[g["id"]],
            "type": gtype,
            "x": 0,
            "y": 0,
            "inputs": _NUM_INPUTS.get(gtype, 2),
            "hasOutput": gtype != "OUTPUT",
            "output": None,
            "inputValues": [False] if gtype == "INPUT" else [],
            "label": g["id"],
        })

    wires, pin_index = [], {}
    types = {g["id"]: g["type"] for g in graph["gates"]}
    for w in graph["wires"]:
        to_id = id_map[w["to"]]
        gtype = types[w["to"]]
        capacity = _NUM_INPUTS.get(gtype, 2)
        if capacity == 0:
            raise ValueError(f"cannot wire into INPUT gate '{w['to']}'")
        idx = pin_index.get(to_id, 0)
        if idx >= capacity:
            raise ValueError(
                f"gate '{w['to']}' ({gtype}) has {capacity} input pin(s), "
                f"wire {len(wires)} would need pin {idx + 1}"
            )
        wires.append({"id": len(wires), "fromId": id_map[w["from"]],
                      "toId": to_id, "toIndex": idx})
        pin_index[to_id] = idx + 1

    _layout_gates(gates, wires)

    return {
        "circuitName": graph.get("circuit_name", "") if circuit_name is None else circuit_name,
        "gates": gates,
        "wires": wires,
        "gateIdCounter": len(gates),
        "wireIdCounter": len(wires),
        "inputCounter": input_count,
        "outputCounter": output_count,
        "exportedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }