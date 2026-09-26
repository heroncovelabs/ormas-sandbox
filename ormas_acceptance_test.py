"""Ormas external acceptance for vbcii1-legacy-foldcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-foldcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_patch_fold():
    _check('oss_tests.py::test_patch_fold')


def test_f2p_watermark_share():
    _check('oss_tests.py::test_watermark_share')


def test_f2p_creep_blank():
    _check('oss_tests.py::test_creep_blank')


def test_f2p_append_inherit():
    _check('oss_tests.py::test_append_inherit')


def test_f2p_after_last():
    _check('oss_tests.py::test_after_last')


def test_f2p_case_dup():
    _check('oss_tests.py::test_case_dup')


def test_f2p_lenient():
    _check('oss_tests.py::test_lenient')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_append_impose():
    _check('reg_tests.py::test_append_impose')


def test_p2p_reimpose():
    _check('reg_tests.py::test_reimpose')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')


def test_p2p_padding():
    _check('reg_tests.py::test_padding')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
