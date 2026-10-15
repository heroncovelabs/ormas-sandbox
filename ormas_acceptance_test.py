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
    check(['template_tests.filter_tests.test_floatformat.FunctionTests.test_zero_values'])


def test_p2p_000():
    check(['template_tests.filter_tests.test_floatformat.FloatformatTests.test_floatformat01', 'template_tests.filter_tests.test_floatformat.FloatformatTests.test_floatformat02', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_float_dunder_method', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_force_grouping', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_infinity', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_inputs', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_low_decimal_precision', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_negative_zero_values', 'template_tests.filter_tests.test_floatformat.FunctionTests.test_unlocalize'])
