"""Tests for the Digital Logic Studio simulation API (alu.logic_unit)."""

import itertools

import pytest

from alu.logic_unit import evaluate_all, simulate_graph, simulate_vectors, truth_table_for


def _full_adder():
    return {
        "circuit_name": "Full Adder",
        "gates": [
            {"id": "A", "type": "INPUT"},
            {"id": "B", "type": "INPUT"},
            {"id": "CIN", "type": "INPUT"},
            {"id": "X1", "type": "XOR"},
            {"id": "X2", "type": "XOR"},
            {"id": "A1", "type": "AND"},
            {"id": "A2", "type": "AND"},
            {"id": "OR1", "type": "OR"},
            {"id": "SUM", "type": "OUTPUT"},
            {"id": "COUT", "type": "OUTPUT"},
        ],
        "wires": [
            {"from": "A", "to": "X1"},
            {"from": "B", "to": "X1"},
            {"from": "X1", "to": "X2"},
            {"from": "CIN", "to": "X2"},
            {"from": "A", "to": "A1"},
            {"from": "B", "to": "A1"},
            {"from": "X1", "to": "A2"},
            {"from": "CIN", "to": "A2"},
            {"from": "A1", "to": "OR1"},
            {"from": "A2", "to": "OR1"},
            {"from": "X2", "to": "SUM"},
            {"from": "OR1", "to": "COUT"},
        ],
    }


def test_evaluate_all_returns_every_gate():
    values = evaluate_all(_full_adder(), {"A": 1, "B": 1, "CIN": 0})
    assert set(values) == {"A", "B", "CIN", "X1", "X2", "A1", "A2", "OR1", "SUM", "COUT"}


def test_evaluate_all_keeps_intermediate_values():
    values = evaluate_all(_full_adder(), {"A": 1, "B": 1, "CIN": 0})
    assert values["X1"] == 0          # 1 XOR 1
    assert values["A1"] == 1          # 1 AND 1
    assert values["X2"] == 0          # 0 XOR 0
    assert values["OR1"] == 1         # carry out
    assert values["SUM"] == 0
    assert values["COUT"] == 1


def test_simulate_graph_is_the_output_subset():
    graph = _full_adder()
    for a, b, cin in itertools.product((0, 1), repeat=3):
        inputs = {"A": a, "B": b, "CIN": cin}
        assert simulate_graph(graph, inputs) == {
            "SUM": evaluate_all(graph, inputs)["SUM"],
            "COUT": evaluate_all(graph, inputs)["COUT"],
        }


def test_simulate_graph_matches_expected_adder_rows():
    graph = _full_adder()
    for a, b, cin in itertools.product((0, 1), repeat=3):
        total = a + b + cin
        assert simulate_graph(graph, {"A": a, "B": b, "CIN": cin}) == {
            "SUM": total & 1,
            "COUT": total >> 1,
        }


def test_evaluate_all_still_validates_missing_inputs():
    with pytest.raises(ValueError, match="missing input values"):
        evaluate_all(_full_adder(), {"A": 1})


def test_simulate_vectors_returns_one_row_per_vector():
    vectors = [
        {"A": 0, "B": 0, "CIN": 0},
        {"A": 1, "B": 0, "CIN": 1},
        {"A": 1, "B": 1, "CIN": 1},
    ]
    assert simulate_vectors(_full_adder(), vectors) == [
        {"SUM": 0, "COUT": 0},
        {"SUM": 0, "COUT": 1},
        {"SUM": 1, "COUT": 1},
    ]


def test_simulate_vectors_keeps_input_order():
    vectors = [{"A": a, "B": b, "CIN": c} for a, b, c in itertools.product((0, 1), repeat=3)]
    rows = simulate_vectors(_full_adder(), vectors)
    assert len(rows) == 8
    for vector, row in zip(vectors, rows):
        assert row["SUM"] == (vector["A"] + vector["B"] + vector["CIN"]) & 1


def test_simulate_vectors_accepts_an_empty_batch():
    assert simulate_vectors(_full_adder(), []) == []


def test_simulate_vectors_rejects_non_mapping_vectors():
    with pytest.raises(ValueError, match="vector 1 must be a mapping"):
        simulate_vectors(_full_adder(), [{"A": 0, "B": 0, "CIN": 0}, [0, 1, 0]])


def test_truth_table_for_covers_every_input_vector():
    rows = truth_table_for(_full_adder())
    assert len(rows) == 8
    assert rows[0] == {
        "inputs": {"A": 0, "B": 0, "CIN": 0},
        "outputs": {"SUM": 0, "COUT": 0},
    }
    assert rows[-1] == {
        "inputs": {"A": 1, "B": 1, "CIN": 1},
        "outputs": {"SUM": 1, "COUT": 1},
    }


def test_truth_table_for_orders_first_input_slowest():
    rows = truth_table_for(_full_adder())
    assert [row["inputs"]["A"] for row in rows] == [0] * 4 + [1] * 4
    assert [row["inputs"]["CIN"] for row in rows] == [0, 1] * 4


def test_truth_table_for_refuses_wide_graphs():
    inputs = [{"id": f"I{i}", "type": "INPUT"} for i in range(5)]
    graph = {
        "circuit_name": "Wide",
        "gates": inputs + [{"id": "Y", "type": "OUTPUT"}],
        "wires": [{"from": "I0", "to": "Y"}],
    }
    with pytest.raises(ValueError, match="truth table limited to 2"):
        truth_table_for(graph, max_inputs=2)
