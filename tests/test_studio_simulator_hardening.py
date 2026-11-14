"""Regression tests for gate-graph validation in alu.logic_unit.

Digital Logic Studio payloads are user-authored, so the simulator must
reject malformed graphs with a clear ValueError instead of a raw KeyError.
"""

import pytest

from alu.logic_unit import simulate_graph


def _graph(gates, wires):
    return {"circuit_name": "Test", "gates": gates, "wires": wires}


def test_wire_to_unknown_gate_is_rejected():
    graph = _graph(
        [{"id": "A", "type": "INPUT"}, {"id": "Y", "type": "OUTPUT"}],
        [{"from": "A", "to": "GHOST"}],
    )
    with pytest.raises(ValueError, match="unknown gate 'GHOST'"):
        simulate_graph(graph, {"A": 0})


def test_wire_from_unknown_gate_is_rejected():
    graph = _graph(
        [{"id": "A", "type": "INPUT"}, {"id": "Y", "type": "OUTPUT"}],
        [{"from": "GHOST", "to": "Y"}],
    )
    with pytest.raises(ValueError, match="unknown gate 'GHOST'"):
        simulate_graph(graph, {"A": 0})


def test_gate_without_type_is_rejected():
    graph = _graph([{"id": "A"}], [])
    with pytest.raises(ValueError, match="each gate needs 'id' and 'type'"):
        simulate_graph(graph, {})


def test_wire_without_endpoints_is_rejected():
    graph = _graph([{"id": "A", "type": "INPUT"}], [{"from": "A"}])
    with pytest.raises(ValueError, match="each wire needs 'from' and 'to'"):
        simulate_graph(graph, {"A": 0})


def test_non_dict_graph_is_rejected():
    with pytest.raises(ValueError, match="graph must be a dict"):
        simulate_graph([], {})


def test_missing_gate_list_is_rejected():
    with pytest.raises(ValueError, match="'gates' and 'wires' lists"):
        simulate_graph({"gates": []}, {})


def test_valid_graph_still_evaluates():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "G", "type": "AND"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [
            {"from": "A", "to": "G"},
            {"from": "B", "to": "G"},
            {"from": "G", "to": "Y"},
        ],
    )
    assert simulate_graph(graph, {"A": 1, "B": 1}) == {"Y": 1}


def test_missing_input_value_names_the_gate():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "G", "type": "AND"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [
            {"from": "A", "to": "G"},
            {"from": "B", "to": "G"},
            {"from": "G", "to": "Y"},
        ],
    )
    with pytest.raises(ValueError, match="missing input values for: B"):
        simulate_graph(graph, {"A": 1})


def test_unconnected_input_still_requires_a_value():
    graph = _graph(
        [{"id": "A", "type": "INPUT"}, {"id": "Y", "type": "OUTPUT"}],
        [],
    )
    with pytest.raises(ValueError, match="missing input values for: A"):
        simulate_graph(graph, {})


def test_extra_input_values_are_ignored():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "N", "type": "NOT"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "N"}, {"from": "N", "to": "Y"}],
    )
    assert simulate_graph(graph, {"A": 0, "UNUSED": 1}) == {"Y": 1}


def test_combinational_cycle_is_reported():
    graph = _graph(
        [
            {"id": "N1", "type": "NOT"},
            {"id": "N2", "type": "NOT"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [
            {"from": "N1", "to": "N2"},
            {"from": "N2", "to": "N1"},
            {"from": "N2", "to": "Y"},
        ],
    )
    with pytest.raises(ValueError, match="combinational cycle"):
        simulate_graph(graph, {})


def test_self_loop_is_reported_as_cycle():
    graph = _graph(
        [{"id": "B", "type": "BUFFER"}, {"id": "Y", "type": "OUTPUT"}],
        [{"from": "B", "to": "B"}, {"from": "B", "to": "Y"}],
    )
    with pytest.raises(ValueError, match="combinational cycle"):
        simulate_graph(graph, {})


@pytest.mark.parametrize(
    "gtype,expected",
    [
        ("AND", {0: 0, 1: 0, 2: 0, 3: 1}),
        ("NAND", {0: 1, 1: 1, 2: 1, 3: 0}),
        ("OR", {0: 0, 1: 1, 2: 1, 3: 1}),
        ("NOR", {0: 1, 1: 0, 2: 0, 3: 0}),
        ("XOR", {0: 0, 1: 1, 2: 1, 3: 0}),
        ("XNOR", {0: 1, 1: 0, 2: 0, 3: 1}),
    ],
)
def test_binary_gate_truth_tables(gtype, expected):
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "G", "type": gtype},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [
            {"from": "A", "to": "G"},
            {"from": "B", "to": "G"},
            {"from": "G", "to": "Y"},
        ],
    )
    for index, out in expected.items():
        assert simulate_graph(graph, {"A": index & 1, "B": (index >> 1) & 1}) == {"Y": out}


@pytest.mark.parametrize("gtype,expected", [("NOT", {0: 1, 1: 0}), ("BUFFER", {0: 0, 1: 1})])
def test_unary_gates(gtype, expected):
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "G", "type": gtype},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "G"}, {"from": "G", "to": "Y"}],
    )
    for value, out in expected.items():
        assert simulate_graph(graph, {"A": value}) == {"Y": out}


def test_unconnected_and_gate_is_rejected():
    graph = _graph(
        [{"id": "G", "type": "AND"}, {"id": "Y", "type": "OUTPUT"}],
        [{"from": "G", "to": "Y"}],
    )
    # An AND with no inputs used to evaluate to 1 because all([]) is True.
    with pytest.raises(ValueError, match="needs at least 2 inputs, found 0"):
        simulate_graph(graph, {})


def test_single_input_and_gate_is_rejected():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "G", "type": "AND"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "G"}, {"from": "G", "to": "Y"}],
    )
    with pytest.raises(ValueError, match="needs at least 2 inputs, found 1"):
        simulate_graph(graph, {"A": 1})


def test_not_gate_with_two_drivers_is_rejected():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "N", "type": "NOT"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [
            {"from": "A", "to": "N"},
            {"from": "B", "to": "N"},
            {"from": "N", "to": "Y"},
        ],
    )
    with pytest.raises(ValueError, match="needs exactly 1 input, found 2"):
        simulate_graph(graph, {"A": 1, "B": 0})


def test_unknown_gate_type_names_the_gate():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "G", "type": "IMPLIES"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "G"}, {"from": "G", "to": "Y"}],
    )
    with pytest.raises(ValueError, match="IMPLIES.*'G'"):
        simulate_graph(graph, {"A": 1})


def test_output_with_two_drivers_is_rejected():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "Y"}, {"from": "B", "to": "Y"}],
    )
    # The second driver used to be ignored silently.
    with pytest.raises(ValueError, match="needs exactly 1 driver, found 2"):
        simulate_graph(graph, {"A": 1, "B": 0})


def test_output_without_driver_is_rejected():
    graph = _graph([{"id": "Y", "type": "OUTPUT"}], [])
    with pytest.raises(ValueError, match="needs exactly 1 driver, found 0"):
        simulate_graph(graph, {})


def test_input_with_incoming_wire_is_rejected():
    graph = _graph(
        [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "Y", "type": "OUTPUT"},
        ],
        [{"from": "A", "to": "B"}, {"from": "B", "to": "Y"}],
    )
    with pytest.raises(ValueError, match="INPUT gate 'B' cannot have incoming wires"):
        simulate_graph(graph, {"A": 1, "B": 0})
