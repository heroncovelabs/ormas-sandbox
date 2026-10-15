"""Ormas adapted public benchmark acceptance; generated, immutable."""
from ormas_acceptance import run

ARGV = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short']
DJANGO = False

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
    check(['tests/test_environment_toctree.py::test_toctree_index'])


def test_p2p_000():
    check(['tests/test_environment_toctree.py::test_process_doc', 'tests/test_environment_toctree.py::test_glob', 'tests/test_environment_toctree.py::test_get_toc_for', 'tests/test_environment_toctree.py::test_get_toc_for_only', 'tests/test_environment_toctree.py::test_get_toc_for_tocdepth', 'tests/test_environment_toctree.py::test_get_toctree_for', 'tests/test_environment_toctree.py::test_get_toctree_for_collapse', 'tests/test_environment_toctree.py::test_get_toctree_for_maxdepth', 'tests/test_environment_toctree.py::test_get_toctree_for_includehidden'])
