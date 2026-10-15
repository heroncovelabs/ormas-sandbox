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
    check(['xor_lookups.tests.XorLookupsTests.test_filter_multiple'])


def test_p2p_000():
    check(['xor_lookups.tests.XorLookupsTests.test_empty_in', 'xor_lookups.tests.XorLookupsTests.test_exclude', 'xor_lookups.tests.XorLookupsTests.test_filter', 'xor_lookups.tests.XorLookupsTests.test_filter_negated', 'xor_lookups.tests.XorLookupsTests.test_pk_q', 'xor_lookups.tests.XorLookupsTests.test_stages'])
