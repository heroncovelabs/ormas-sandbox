"""Ormas adapted public benchmark acceptance; generated, immutable."""
from ormas_acceptance import run

ARGV = ['env', 'PYTHONPATH=.', 'python3', 'tests/runtests.py', '--parallel', '1']
DJANGO = True

def check(selectors):
    result = run(ARGV + selectors, timeout_s=60)
    code, output = result['returncode'], result['output']
    if code not in (0, 1):
        raise RuntimeError('candidate setup/collection/timeout: ' + output[-3000:])
    if code and (('Ran ' not in output if DJANGO else ' failed' not in output)
                 or 'ERROR collecting' in output or 'Failed to import test module' in output):
        raise RuntimeError('candidate did not execute behavioral tests: ' + output[-3000:])
    assert code == 0, output[-6000:]


def test_f2p_000():
    check(['template_tests.filter_tests.test_escapeseq.EscapeseqTests.test_autoescape_off'])


def test_f2p_001():
    check(['template_tests.filter_tests.test_escapeseq.EscapeseqTests.test_basic'])


def test_f2p_002():
    check(['template_tests.filter_tests.test_escapeseq.EscapeseqTests.test_chain_join'])


def test_f2p_003():
    check(['template_tests.filter_tests.test_escapeseq.EscapeseqTests.test_chain_join_autoescape_off'])
