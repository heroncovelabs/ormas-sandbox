"""Ormas external acceptance for vbv1-py-event-ledger.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-event-ledger@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_open_deposit_balance():
    _check('test_ledger.py::test_open_deposit_balance')


def test_f2p_withdraw_and_insufficient():
    _check('test_ledger.py::test_withdraw_and_insufficient_funds')


def test_f2p_validation_errors():
    _check('test_ledger.py::test_validation_errors')


def test_f2p_transfer_two_events():
    _check('test_ledger.py::test_transfer_moves_funds_with_two_events')


def test_f2p_transfer_atomic():
    _check('test_ledger.py::test_transfer_is_atomic_on_insufficient_funds')


def test_f2p_rebuild_from_history():
    _check('test_ledger.py::test_rebuild_from_history_matches_live_state')


def test_f2p_snapshot_equals_replay():
    _check('test_ledger.py::test_snapshot_equals_replay_of_history')


def test_p2p_construct():
    _check('test_ledger.py::test_construct')
