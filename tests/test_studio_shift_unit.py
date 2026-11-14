"""Tests for the Digital Logic Studio shift unit (alu.shift_unit)."""

import itertools

import pytest

from alu.logic_unit import simulate_graph
from alu.shift_unit import (
    build_shift_arithmetic_right_graph,
    build_shift_left_graph,
    build_shift_right_graph,
    shift_unit,
)


def _drive(width, value, amount):
    return {
        **{f"X{i}": (value >> i) & 1 for i in range(width)},
        **{f"A{k}": (amount >> k) & 1 for k in range((width - 1).bit_length())},
    }


def _read(graph, width, value, amount):
    outputs = simulate_graph(graph, _drive(width, value, amount))
    return sum(outputs[f"Y{i}"] << i for i in range(width))


def test_shift_left_moves_bits_up():
    assert shift_unit(0b0011, 2, "SLL", 4) == 0b1100
    assert shift_unit(0b1010, 1, "SLL", 4) == 0b0100


def test_shift_right_logical_moves_bits_down():
    assert shift_unit(0b1100, 2, "SRL", 4) == 0b0011
    assert shift_unit(0b1000, 1, "SRL", 4) == 0b0100


def test_shift_by_zero_keeps_the_value():
    for mode in ("SLL", "SRL", "SRA"):
        assert shift_unit(0b1011, 0, mode, 4) == 0b1011


def test_shift_masks_the_value_to_the_width():
    # Bits above the width are dropped before shifting, not after.
    assert shift_unit(0xF0, 1, "SRL", 4) == 0
    assert shift_unit(0xFF, 1, "SLL", 4) == 0b1110


def test_shift_rejects_unknown_modes():
    with pytest.raises(ValueError, match="mode must be one of SLL, SRL, SRA"):
        shift_unit(1, 1, "ROL", 4)


def test_shift_rejects_an_amount_outside_the_width():
    with pytest.raises(ValueError, match="out of range for a 4-bit shifter"):
        shift_unit(1, 4, "SLL", 4)


def test_shift_rejects_a_negative_amount():
    with pytest.raises(ValueError, match="amount must be non-negative"):
        shift_unit(1, -1, "SRL", 4)


def test_arithmetic_shift_replicates_the_sign_bit():
    assert shift_unit(0b1000, 1, "SRA", 4) == 0b1100
    assert shift_unit(0b1000, 3, "SRA", 4) == 0b1111
    assert shift_unit(0b1100, 2, "SRA", 4) == 0b1111


def test_arithmetic_shift_of_a_positive_value_is_logical():
    for value in range(8):
        for amount in range(4):
            assert shift_unit(value, amount, "SRA", 4) == shift_unit(value, amount, "SRL", 4)


def test_left_shifter_graph_matches_the_model():
    graph = build_shift_left_graph(width=4)
    for value, amount in itertools.product(range(16), range(4)):
        assert _read(graph, 4, value, amount) == shift_unit(value, amount, "SLL", 4)


def test_left_shifter_graph_has_a_stage_per_amount_bit():
    graph = build_shift_left_graph(width=4)
    labels = {gate["id"] for gate in graph["gates"]}
    assert {"X0", "X3", "A0", "A1", "Y0", "Y3"} <= labels
    assert "A2" not in labels
    assert graph["circuit_name"] == "4-bit Logical Left Shifter"


def test_one_bit_left_shifter_is_a_passthrough():
    graph = build_shift_left_graph(width=1)
    assert _read(graph, 1, 1, 0) == 1


def test_right_shifter_graph_matches_the_model():
    graph = build_shift_right_graph(width=4)
    for value, amount in itertools.product(range(16), range(4)):
        assert _read(graph, 4, value, amount) == shift_unit(value, amount, "SRL", 4)


def test_right_shifter_graph_fills_with_zeros():
    graph = build_shift_right_graph(width=4)
    assert _read(graph, 4, 0b1111, 3) == 0b0001
    assert _read(graph, 4, 0b1111, 1) == 0b0111
    assert graph["circuit_name"] == "4-bit Logical Right Shifter"


def test_arithmetic_right_shifter_graph_matches_the_model():
    graph = build_shift_arithmetic_right_graph(width=4)
    for value, amount in itertools.product(range(16), range(4)):
        assert _read(graph, 4, value, amount) == shift_unit(value, amount, "SRA", 4)


def test_arithmetic_right_shifter_keeps_the_sign():
    graph = build_shift_arithmetic_right_graph(width=4)
    assert _read(graph, 4, 0b1000, 1) == 0b1100
    assert _read(graph, 4, 0b1001, 2) == 0b1110
    assert graph["circuit_name"] == "4-bit Arithmetic Right Shifter"


def test_arithmetic_and_logical_right_shifters_differ_only_on_negatives():
    logical = build_shift_right_graph(width=4)
    arithmetic = build_shift_arithmetic_right_graph(width=4)
    assert _read(logical, 4, 0b1000, 1) != _read(arithmetic, 4, 0b1000, 1)
    for value, amount in itertools.product(range(8), range(4)):
        assert _read(logical, 4, value, amount) == _read(arithmetic, 4, value, amount)
