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
