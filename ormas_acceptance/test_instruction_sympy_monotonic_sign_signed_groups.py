"""Authored by Ormas from the public SymPy monotonic-sign instruction.

These are independent Ormas acceptance tests, not VulcanBench scoring tests.
Source: VulcanBench 36e2764128f1010b9590714e851ac9dfda95ff68,
tasks/frontier-v5/sympy-monotonic-sign-signed-groups/instruction.md.
Only that instruction and pristine public upstream code/tests were used.
No private hidden directory or gold scoring file was opened during authoring.
"""

import pytest
from sympy import symbols


@pytest.mark.parametrize(
    "sign,constant,property_name",
    [
        (1, -2, "is_positive"),
        (1, -3, "is_nonnegative"),
        (-1, 3, "is_nonpositive"),
        (-1, 2, "is_negative"),
    ],
)
def test_same_signed_integer_terms_combine_guaranteed_bounds(sign, constant, property_name):
    a, b, c = symbols("a b c", positive=True, integer=True)
    expression = sign * (a + b + c) + constant
    assert getattr(expression, property_name) is True


def test_mixed_signed_terms_remain_unknown():
    a, b, c = symbols("a b c", positive=True, integer=True)
    expression = a + b - c - 2
    assert expression.is_positive is None


def test_positive_terms_without_integer_bounds_do_not_imply_a_sign():
    a, b, c = symbols("a b c", positive=True)
    assert (a + b + c - 2).is_positive is None
