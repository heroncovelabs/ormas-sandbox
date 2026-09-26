"""Ormas external acceptance for vbcii1-oss-pygments-transparent-color.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-pygments-transparent-color@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_accepted():
    _check('oss_tests.py::test_transparent_accepted_in_style_definition')


def test_f2p_css_emitted():
    _check('oss_tests.py::test_transparent_emitted_in_css')


def test_f2p_not_mangled():
    _check('oss_tests.py::test_transparent_not_hex_mangled')


def test_p2p_hex():
    _check('reg_tests.py::test_hex_colors_still_work')


def test_p2p_var_calc():
    _check('reg_tests.py::test_var_and_calc_pass_through')


def test_p2p_invalid_rejected():
    _check('reg_tests.py::test_invalid_color_still_rejected')


def test_p2p_default_style():
    _check('reg_tests.py::test_default_style_renders')
