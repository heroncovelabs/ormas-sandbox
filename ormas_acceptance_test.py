"""Ormas external acceptance for vbcii1-oss-click-custom-version-option.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-click-custom-version-option@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_prints_and_exits():
    _check('oss_tests.py::test_prints_callback_output_and_exits')


def test_f2p_param_decls():
    _check('oss_tests.py::test_custom_param_decls')


def test_f2p_receives_context():
    _check('oss_tests.py::test_callback_receives_context')


def test_f2p_eager():
    _check('oss_tests.py::test_eager_before_required_arguments')


def test_p2p_version_option():
    _check('reg_tests.py::test_version_option_still_works')


def test_p2p_plain_command():
    _check('reg_tests.py::test_plain_command_runs')


def test_p2p_help():
    _check('reg_tests.py::test_help_still_renders')
