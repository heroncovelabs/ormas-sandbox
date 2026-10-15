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
    check(['responses.test_fileresponse.FileResponseTests.test_compressed_response'])


def test_p2p_000():
    check(['responses.test_fileresponse.FileResponseTests.test_buffer_explicit_absolute_filename', 'responses.test_fileresponse.FileResponseTests.test_content_disposition_buffer', 'responses.test_fileresponse.FileResponseTests.test_content_disposition_buffer_attachment', 'responses.test_fileresponse.FileResponseTests.test_content_disposition_buffer_explicit_filename', 'responses.test_fileresponse.FileResponseTests.test_content_disposition_escaping', 'responses.test_fileresponse.FileResponseTests.test_content_disposition_file', 'responses.test_fileresponse.FileResponseTests.test_content_length_buffer', 'responses.test_fileresponse.FileResponseTests.test_content_length_file', 'responses.test_fileresponse.FileResponseTests.test_content_length_nonzero_starting_position_buffer', 'responses.test_fileresponse.FileResponseTests.test_content_length_nonzero_starting_position_file', 'responses.test_fileresponse.FileResponseTests.test_content_length_nonzero_starting_position_file_seekable_no_tell', 'responses.test_fileresponse.FileResponseTests.test_content_type_buffer', 'responses.test_fileresponse.FileResponseTests.test_content_type_buffer_explicit', 'responses.test_fileresponse.FileResponseTests.test_content_type_buffer_explicit_default', 'responses.test_fileresponse.FileResponseTests.test_content_type_buffer_named', 'responses.test_fileresponse.FileResponseTests.test_content_type_file', 'responses.test_fileresponse.FileResponseTests.test_file_from_named_pipe_response', 'responses.test_fileresponse.FileResponseTests.test_repr', 'responses.test_fileresponse.FileResponseTests.test_response_buffer', 'responses.test_fileresponse.FileResponseTests.test_response_nonzero_starting_position'])


def test_p2p_020():
    check(['responses.test_fileresponse.FileResponseTests.test_unicode_attachment'])
