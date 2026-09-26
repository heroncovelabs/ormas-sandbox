"""Ormas external acceptance for vbv1-py-config-parse.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-config-parse@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_comments_blanks():
    _check('test_parse.py::test_comments_and_blanks')


def test_f2p_basic_whitespace():
    _check('test_parse.py::test_basic_and_whitespace')


def test_f2p_quoting():
    _check('test_parse.py::test_quoting')


def test_f2p_escapes():
    _check('test_parse.py::test_escapes_in_quotes')


def test_f2p_inline_comments():
    _check('test_parse.py::test_inline_comments')


def test_f2p_bool_null():
    _check('test_parse.py::test_bool_null_coercion')


def test_f2p_int_coercion():
    _check('test_parse.py::test_int_coercion')


def test_f2p_float_coercion():
    _check('test_parse.py::test_float_coercion')


def test_f2p_empty_duplicate():
    _check('test_parse.py::test_empty_and_duplicate')


def test_f2p_invalid():
    _check('test_parse.py::test_invalid_raises')


def test_p2p_imports():
    _check('test_parse.py::test_module_imports')
