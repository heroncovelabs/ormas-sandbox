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
    check(['tests/test_directive_code.py::test_LiteralIncludeReader_dedent_and_append_and_prepend'])


def test_p2p_000():
    check(['tests/test_directive_code.py::test_LiteralIncludeReader', 'tests/test_directive_code.py::test_LiteralIncludeReader_lineno_start', 'tests/test_directive_code.py::test_LiteralIncludeReader_pyobject1', 'tests/test_directive_code.py::test_LiteralIncludeReader_pyobject2', 'tests/test_directive_code.py::test_LiteralIncludeReader_pyobject3', 'tests/test_directive_code.py::test_LiteralIncludeReader_pyobject_and_lines', 'tests/test_directive_code.py::test_LiteralIncludeReader_lines1', 'tests/test_directive_code.py::test_LiteralIncludeReader_lines2', 'tests/test_directive_code.py::test_LiteralIncludeReader_lines_and_lineno_match1', 'tests/test_directive_code.py::test_LiteralIncludeReader_lines_and_lineno_match2', 'tests/test_directive_code.py::test_LiteralIncludeReader_lines_and_lineno_match3', 'tests/test_directive_code.py::test_LiteralIncludeReader_start_at', 'tests/test_directive_code.py::test_LiteralIncludeReader_start_after', 'tests/test_directive_code.py::test_LiteralIncludeReader_start_after_and_lines', 'tests/test_directive_code.py::test_LiteralIncludeReader_start_at_and_lines', 'tests/test_directive_code.py::test_LiteralIncludeReader_missing_start_and_end', 'tests/test_directive_code.py::test_LiteralIncludeReader_end_before', 'tests/test_directive_code.py::test_LiteralIncludeReader_prepend', 'tests/test_directive_code.py::test_LiteralIncludeReader_dedent', 'tests/test_directive_code.py::test_LiteralIncludeReader_tabwidth'])


def test_p2p_020():
    check(['tests/test_directive_code.py::test_LiteralIncludeReader_tabwidth_dedent', 'tests/test_directive_code.py::test_LiteralIncludeReader_diff', 'tests/test_directive_code.py::test_code_block', 'tests/test_directive_code.py::test_force_option', 'tests/test_directive_code.py::test_code_block_caption_html', 'tests/test_directive_code.py::test_code_block_caption_latex', 'tests/test_directive_code.py::test_code_block_namedlink_latex', 'tests/test_directive_code.py::test_code_block_emphasize_latex', 'tests/test_directive_code.py::test_literal_include', 'tests/test_directive_code.py::test_literal_include_block_start_with_comment_or_brank', 'tests/test_directive_code.py::test_literal_include_linenos', 'tests/test_directive_code.py::test_literalinclude_file_whole_of_emptyline', 'tests/test_directive_code.py::test_literalinclude_caption_html', 'tests/test_directive_code.py::test_literalinclude_caption_latex', 'tests/test_directive_code.py::test_literalinclude_namedlink_latex', 'tests/test_directive_code.py::test_literalinclude_classes', 'tests/test_directive_code.py::test_literalinclude_pydecorators', 'tests/test_directive_code.py::test_code_block_highlighted', 'tests/test_directive_code.py::test_linenothreshold', 'tests/test_directive_code.py::test_code_block_dedent'])
