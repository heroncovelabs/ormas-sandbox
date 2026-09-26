"""Ormas external acceptance for vbv1-py-csv-export-feature.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-csv-export-feature@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
with pytest inside the isolated candidate container, and asserts it passed.

A check that ran and failed is an assertion failure. A check that could not
run (collection/import/usage error, no tests collected, timeout) raises
RuntimeError instead, so the verifier reports a setup problem rather than a
behavioral failure.
"""
import re

from ormas_acceptance import run

PYTEST = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short']
_ERRORS = re.compile(r"\b\d+ errors?\b")


def _check(selector):
    result = run(PYTEST + [selector], timeout_s=60)
    output = result["output"]
    lines = [line for line in output.splitlines() if line.strip()]
    summary = lines[-1] if lines else ""
    if result["returncode"] not in (0, 1) or _ERRORS.search(summary):
        raise RuntimeError(
            "candidate check did not complete (exit %s): %s"
            % (result["returncode"], output[-4000:])
        )
    assert result["returncode"] == 0, output[-4000:]


def test_f2p_header_and_simple_rows():
    _check('test_csv.py::test_header_and_simple_rows')


def test_f2p_field_with_comma_is_quoted():
    _check('test_csv.py::test_field_with_comma_is_quoted')


def test_f2p_double_quote_is_doubled():
    _check('test_csv.py::test_double_quote_is_doubled_and_quoted')


def test_f2p_newline_in_field_is_quoted():
    _check('test_csv.py::test_newline_in_field_is_quoted')


def test_f2p_carriage_return_in_field_is_quoted():
    _check('test_csv.py::test_carriage_return_in_field_is_quoted')


def test_f2p_none_is_empty_field():
    _check('test_csv.py::test_none_is_empty_field')


def test_f2p_integer_value_is_stringified():
    _check('test_csv.py::test_integer_value_is_stringified')


def test_f2p_columns_follow_first_row_order():
    _check('test_csv.py::test_columns_follow_first_row_order')


def test_f2p_empty_rows_is_empty_string():
    _check('test_csv.py::test_empty_rows_is_empty_string')


def test_p2p_json():
    _check('test_json.py')
