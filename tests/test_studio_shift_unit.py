"""Tests for the Digital Logic Studio shift unit (alu.shift_unit)."""

import pytest

from alu.shift_unit import shift_unit


def test_shift_left_moves_bits_up():
    assert shift_unit(0b0011, 2, "SLL", 4) == 0b1100
    assert shift_unit(0b1010, 1, "SLL", 4) == 0b0100


def test_shift_right_logical_moves_bits_down():
    assert shift_unit(0b1100, 2, "SRL", 4) == 0b0011
    assert shift_unit(0b1000, 1, "SRL", 4) == 0b0100


def test_shift_by_zero_keeps_the_value():
    for mode in ("SLL", "SRL"):
        assert shift_unit(0b1011, 0, mode, 4) == 0b1011


def test_shift_masks_the_value_to_the_width():
    # Bits above the width are dropped before shifting, not after.
    assert shift_unit(0xF0, 1, "SRL", 4) == 0
    assert shift_unit(0xFF, 1, "SLL", 4) == 0b1110


def test_shift_rejects_unknown_modes():
    with pytest.raises(ValueError, match="mode must be one of SLL, SRL"):
        shift_unit(1, 1, "ROL", 4)


def test_shift_rejects_an_amount_outside_the_width():
    with pytest.raises(ValueError, match="out of range for a 4-bit shifter"):
        shift_unit(1, 4, "SLL", 4)


def test_shift_rejects_a_negative_amount():
    with pytest.raises(ValueError, match="amount must be non-negative"):
        shift_unit(1, -1, "SRL", 4)
