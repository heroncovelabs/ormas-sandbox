"""Ormas external acceptance for vbcii1-legacy-lockcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-lockcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_renew_decay():
    _check('oss_tests.py::test_renew_decay')


def test_f2p_grace_reclaim():
    _check('oss_tests.py::test_grace_reclaim')


def test_f2p_longname_cap():
    _check('oss_tests.py::test_longname_cap')


def test_f2p_final_tick():
    _check('oss_tests.py::test_final_tick')


def test_f2p_idempotent_release():
    _check('oss_tests.py::test_idempotent_release')


def test_f2p_id_case():
    _check('oss_tests.py::test_id_case')


def test_f2p_trailing():
    _check('oss_tests.py::test_trailing')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_flow():
    _check('reg_tests.py::test_flow')


def test_p2p_sweep():
    _check('reg_tests.py::test_sweep')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
