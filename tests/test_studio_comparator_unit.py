"""Tests for the Digital Logic Studio comparator unit (alu.comparator_unit)."""

import pytest

from alu.comparator_unit import compare


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
