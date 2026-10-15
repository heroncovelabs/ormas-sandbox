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
    check(['template_tests.test_autoreloader.TemplateReloadTests.test_template_dirs_ignore_empty_path'])


def test_p2p_000():
    check(['template_tests.test_autoreloader.Jinja2TemplateReloadTests.test_get_template_directories', 'template_tests.test_autoreloader.Jinja2TemplateReloadTests.test_reset_all_loaders', 'template_tests.test_autoreloader.Jinja2TemplateReloadTests.test_watch_for_template_changes', 'template_tests.test_autoreloader.TemplateReloadTests.test_get_template_directories', 'template_tests.test_autoreloader.TemplateReloadTests.test_non_template_changed', 'template_tests.test_autoreloader.TemplateReloadTests.test_non_template_changed_in_template_directory', 'template_tests.test_autoreloader.TemplateReloadTests.test_reset_all_loaders', 'template_tests.test_autoreloader.TemplateReloadTests.test_template_changed', 'template_tests.test_autoreloader.TemplateReloadTests.test_template_dirs_normalized_to_paths', 'template_tests.test_autoreloader.TemplateReloadTests.test_watch_for_template_changes'])
