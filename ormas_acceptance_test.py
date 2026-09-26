"""Ormas external acceptance for vbcii1-oss-packaging-interpreter-tag-identifier.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-packaging-interpreter-tag-identifier@88df1c9756ff93105190591e05cd97ad28d4dea5)
with pytest inside the isolated candidate container, and asserts it passed.

A check that ran and failed is an assertion failure. A check that could not
run (collection/import/usage error, no tests collected, timeout) raises
RuntimeError instead, so the verifier reports a setup problem rather than a
behavioral failure.
"""
import re

from ormas_acceptance import run

PYTEST = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short', '-o', 'pythonpath=src']
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


def test_f2p_non_identifier_rejected():
    _check('oss_tests.py::test_non_identifier_interpreter_rejected')


def test_f2p_dotted_not_split():
    _check('oss_tests.py::test_dotted_interpreter_not_split_into_tags')


def test_f2p_wheel_invalid_interpreter():
    _check('oss_tests.py::test_wheel_filename_invalid_interpreter_rejected')


def test_f2p_wheel_plus_interpreter():
    _check('oss_tests.py::test_wheel_filename_plus_interpreter_rejected')


def test_p2p_identifiers_accepted():
    _check('reg_tests.py::test_identifier_interpreters_accepted')


def test_p2p_compressed_sets():
    _check('reg_tests.py::test_compressed_tag_sets_still_expand')


def test_p2p_empty_component():
    _check('reg_tests.py::test_empty_component_still_rejected')


def test_p2p_component_count():
    _check('reg_tests.py::test_wrong_component_count_still_rejected')


def test_p2p_valid_wheel():
    _check('reg_tests.py::test_valid_wheel_filename_still_parses')
