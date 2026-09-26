"""Ormas external acceptance for vbv1-py-paginate-cursor.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-paginate-cursor@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_is_after_strict():
    _check('test_pagination.py::test_is_after_is_strict')


def test_f2p_last_page_no_next():
    _check('test_pagination.py::test_last_page_has_no_next_cursor')


def test_f2p_full_walk():
    _check('test_pagination.py::test_full_walk_no_dupes_no_gaps')


def test_f2p_contiguous_pages():
    _check('test_pagination.py::test_pages_are_contiguous_no_boundary_repeat')


def test_f2p_tie_break():
    _check('test_pagination.py::test_tie_break_on_id_within_same_timestamp')


def test_f2p_limit_over_size():
    _check('test_pagination.py::test_limit_larger_than_dataset')


def test_p2p_first_page():
    _check('test_pagination.py::test_first_page_basic')


def test_p2p_empty():
    _check('test_pagination.py::test_empty_repository')
