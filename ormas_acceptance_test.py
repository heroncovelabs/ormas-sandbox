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
    check(['sympy/crypto/tests/test_crypto.py::test_encode_morse'])


def test_p2p_000():
    check(['sympy/crypto/tests/test_crypto.py::test_cycle_list', 'sympy/crypto/tests/test_crypto.py::test_encipher_shift', 'sympy/crypto/tests/test_crypto.py::test_encipher_rot13', 'sympy/crypto/tests/test_crypto.py::test_encipher_affine', 'sympy/crypto/tests/test_crypto.py::test_encipher_atbash', 'sympy/crypto/tests/test_crypto.py::test_encipher_substitution', 'sympy/crypto/tests/test_crypto.py::test_check_and_join', 'sympy/crypto/tests/test_crypto.py::test_encipher_vigenere', 'sympy/crypto/tests/test_crypto.py::test_decipher_vigenere', 'sympy/crypto/tests/test_crypto.py::test_encipher_hill', 'sympy/crypto/tests/test_crypto.py::test_decipher_hill', 'sympy/crypto/tests/test_crypto.py::test_encipher_bifid5', 'sympy/crypto/tests/test_crypto.py::test_bifid5_square', 'sympy/crypto/tests/test_crypto.py::test_decipher_bifid5', 'sympy/crypto/tests/test_crypto.py::test_encipher_bifid6', 'sympy/crypto/tests/test_crypto.py::test_decipher_bifid6', 'sympy/crypto/tests/test_crypto.py::test_bifid6_square', 'sympy/crypto/tests/test_crypto.py::test_rsa_public_key', 'sympy/crypto/tests/test_crypto.py::test_rsa_private_key', 'sympy/crypto/tests/test_crypto.py::test_rsa_large_key'])


def test_p2p_020():
    check(['sympy/crypto/tests/test_crypto.py::test_kid_rsa_public_key', 'sympy/crypto/tests/test_crypto.py::test_kid_rsa_private_key', 'sympy/crypto/tests/test_crypto.py::test_encipher_kid_rsa', 'sympy/crypto/tests/test_crypto.py::test_decipher_kid_rsa', 'sympy/crypto/tests/test_crypto.py::test_decode_morse', 'sympy/crypto/tests/test_crypto.py::test_lfsr_sequence', 'sympy/crypto/tests/test_crypto.py::test_lfsr_autocorrelation', 'sympy/crypto/tests/test_crypto.py::test_lfsr_connection_polynomial', 'sympy/crypto/tests/test_crypto.py::test_elgamal_private_key', 'sympy/crypto/tests/test_crypto.py::test_elgamal', 'sympy/crypto/tests/test_crypto.py::test_dh_private_key', 'sympy/crypto/tests/test_crypto.py::test_dh_public_key', 'sympy/crypto/tests/test_crypto.py::test_dh_shared_key', 'sympy/crypto/tests/test_crypto.py::test_padded_key', 'sympy/crypto/tests/test_crypto.py::test_bifid', 'sympy/crypto/tests/test_crypto.py::test_encipher_decipher_gm', 'sympy/crypto/tests/test_crypto.py::test_gm_private_key', 'sympy/crypto/tests/test_crypto.py::test_gm_public_key', 'sympy/crypto/tests/test_crypto.py::test_encipher_decipher_bg', 'sympy/crypto/tests/test_crypto.py::test_bg_private_key'])
