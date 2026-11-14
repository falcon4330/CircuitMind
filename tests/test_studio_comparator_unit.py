"""Tests for the Digital Logic Studio comparator unit (alu.comparator_unit)."""

import itertools

import pytest

from alu.comparator_unit import build_comparator_graph, compare
from alu.logic_unit import simulate_graph


def _drive(width, a, b):
    return {
        **{f"A{i}": (a >> i) & 1 for i in range(width)},
        **{f"B{i}": (b >> i) & 1 for i in range(width)},
    }


def _flags(graph, width, a, b):
    return simulate_graph(graph, _drive(width, a, b))


def test_compare_reports_all_three_flags():
    assert compare(3, 5) == {"eq": 0, "gt": 0, "lt": 1}
    assert compare(5, 3) == {"eq": 0, "gt": 1, "lt": 0}
    assert compare(5, 5) == {"eq": 1, "gt": 0, "lt": 0}


def test_compare_masks_operands_to_the_width():
    assert compare(0b10011, 0b0011, 4) == {"eq": 1, "gt": 0, "lt": 0}
    assert compare(0x1B, 0x0C, 4) == {"eq": 0, "gt": 0, "lt": 1}


def test_compare_rejects_a_non_positive_width():
    with pytest.raises(ValueError, match="width must be at least 1"):
        compare(1, 2, 0)


def test_comparator_graph_matches_the_model_on_equality():
    graph = build_comparator_graph(width=4)
    for a, b in itertools.product(range(16), repeat=2):
        assert _flags(graph, 4, a, b)["EQ"] == compare(a, b, 4)["eq"]


def test_comparator_graph_builds_equality_per_bit():
    graph = build_comparator_graph(width=3)
    labels = {gate["id"] for gate in graph["gates"]}
    assert {"eq0", "eq1", "eq2", "nA0", "nB2"} <= labels
    assert graph["circuit_name"] == "3-bit Comparator"


def test_one_bit_comparator_equality_matches_the_bit():
    graph = build_comparator_graph(width=1)
    assert _flags(graph, 1, 1, 1)["EQ"] == 1
    assert _flags(graph, 1, 1, 0)["EQ"] == 0


def test_comparator_graph_matches_the_model_on_greater_than():
    graph = build_comparator_graph(width=4)
    for a, b in itertools.product(range(16), repeat=2):
        assert _flags(graph, 4, a, b)["GT"] == compare(a, b, 4)["gt"]


def test_greater_than_is_decided_by_the_highest_differing_bit():
    graph = build_comparator_graph(width=4)
    assert _flags(graph, 4, 0b1000, 0b0111)["GT"] == 1
    assert _flags(graph, 4, 0b0111, 0b1000)["GT"] == 0
    assert _flags(graph, 4, 0b0101, 0b0011)["GT"] == 1
    assert _flags(graph, 4, 0b0011, 0b0101)["GT"] == 0
    assert _flags(graph, 4, 0b1001, 0b1001)["GT"] == 0


def test_comparator_graph_matches_the_model_on_less_than():
    graph = build_comparator_graph(width=4)
    for a, b in itertools.product(range(16), repeat=2):
        assert _flags(graph, 4, a, b)["LT"] == compare(a, b, 4)["lt"]


def test_comparator_flags_are_exactly_one_of_three():
    graph = build_comparator_graph(width=4)
    for a, b in itertools.product(range(16), repeat=2):
        flags = _flags(graph, 4, a, b)
        assert sorted(flags) == ["EQ", "GT", "LT"]
        assert sum(flags.values()) == 1
