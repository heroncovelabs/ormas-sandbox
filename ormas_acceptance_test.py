"""Ormas external acceptance for vbcii1-legacy-syncpeer-wire-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-syncpeer-wire-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_version_negotiation():
    _check('oss_tests.py::test_version_negotiation')


def test_f2p_session_identity():
    _check('oss_tests.py::test_session_identity')


def test_f2p_keys_ordering():
    _check('oss_tests.py::test_keys_ordering')


def test_f2p_put_overwrite_echo():
    _check('oss_tests.py::test_put_overwrite_echo')


def test_f2p_value_truncation():
    _check('oss_tests.py::test_value_truncation')


def test_f2p_goodbye_count():
    _check('oss_tests.py::test_goodbye_count')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_wire_parity():
    _check('oss_tests.py::test_full_wire_parity')


def test_p2p_basic_kv():
    _check('reg_tests.py::test_basic_kv')


def test_p2p_handshake_errors():
    _check('reg_tests.py::test_handshake_errors')


def test_p2p_fmt_errors():
    _check('reg_tests.py::test_fmt_errors')


def test_p2p_persistence_across_connections():
    _check('reg_tests.py::test_persistence_across_connections')
