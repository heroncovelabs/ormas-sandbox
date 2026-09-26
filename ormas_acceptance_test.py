"""Ormas external acceptance for vbv1-py-txn-kvstore.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-txn-kvstore@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_autocommit():
    _check('test_txnkv.py::test_autocommit_without_transaction')


def test_f2p_rollback_value_and_absence():
    _check('test_txnkv.py::test_rollback_restores_prior_value_and_absence')


def test_f2p_rollback_deleted_key():
    _check('test_txnkv.py::test_rollback_restores_deleted_key')


def test_f2p_commit_keeps_changes():
    _check('test_txnkv.py::test_commit_keeps_changes')


def test_f2p_nested_commit_outer_rollback():
    _check('test_txnkv.py::test_nested_commit_then_outer_rollback_undoes_everything')


def test_f2p_nested_inner_rollback():
    _check('test_txnkv.py::test_nested_inner_rollback_leaves_outer_intact')


def test_f2p_rollback_reverse_order():
    _check('test_txnkv.py::test_rollback_replays_multiple_writes_in_reverse')


def test_f2p_commit_without_txn():
    _check('test_txnkv.py::test_commit_without_transaction_raises')


def test_f2p_keys_reflects_txn():
    _check('test_txnkv.py::test_keys_reflects_transaction_state')


def test_p2p_construct():
    _check('test_txnkv.py::test_construct')
