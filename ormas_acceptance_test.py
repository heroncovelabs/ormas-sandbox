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
    check(['dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_parameters'])


def test_p2p_000():
    check(['dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_accent', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_basic', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_column', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_crash_password_does_not_leak', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_nopass', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_passfile', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_service', 'dbshell.test_postgresql.PostgreSqlDbshellCommandTestCase.test_ssl_certificate'])
