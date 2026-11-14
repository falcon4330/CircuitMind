"""Tests for the gate-JSON export of the Digital Logic Studio (alu.logic_unit)."""

import pytest

from alu.logic_unit import build_logic_unit_graph, to_gate_json


def _wire_gate():
    return {
        "circuit_name": "Wire",
        "gates": [{"id": "A", "type": "INPUT"}, {"id": "Y", "type": "OUTPUT"}],
        "wires": [{"from": "A", "to": "Y"}],
    }


def test_export_rejects_a_graph_without_wires():
    with pytest.raises(ValueError, match="'gates' and 'wires'"):
        to_gate_json({"circuit_name": "Broken"})


def test_export_rejects_a_wire_to_an_unknown_gate():
    graph = _wire_gate()
    graph["wires"].append({"from": "A", "to": "MISSING"})
    with pytest.raises(ValueError, match="wire references unknown gate 'MISSING'"):
        to_gate_json(graph)


def test_export_builds_the_logic_unit_payload():
    payload = to_gate_json(build_logic_unit_graph(width=1))
    labels = [gate["label"] for gate in payload["gates"]]
    assert labels[:4] == ["A0", "B0", "S0", "S1"]
    assert payload["inputCounter"] == 4
    assert payload["outputCounter"] == 1


def test_export_rejects_duplicate_gate_ids():
    graph = _wire_gate()
    graph["gates"].append({"id": "A", "type": "INPUT"})
    with pytest.raises(ValueError, match="duplicate gate id 'A'"):
        to_gate_json(graph)


def test_export_assigns_one_numeric_id_per_gate():
    payload = to_gate_json(build_logic_unit_graph(width=1))
    ids = [gate["id"] for gate in payload["gates"]]
    assert ids == list(range(len(ids)))
    assert payload["gateIdCounter"] == len(ids)
