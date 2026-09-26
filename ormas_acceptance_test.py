"""Ormas external acceptance for vbv1-oss-inflection-titleize.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/oss-inflection-titleize@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_leading_accented_word():
    _check('test_titleize.py::test_titleize_leading_accented_word')


def test_f2p_already_titlecased_accented():
    _check('test_titleize.py::test_titleize_already_titlecased_accented_word')


def test_p2p_ascii_phrase():
    _check('test_titleize.py::test_titleize_ascii_phrase')


def test_p2p_camelcase():
    _check('test_titleize.py::test_titleize_camelcase')


def test_p2p_midword_accent():
    _check('test_titleize.py::test_titleize_midword_accent')
