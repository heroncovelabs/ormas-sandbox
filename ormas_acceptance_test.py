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
    check(['auth_tests.test_forms.UserCreationFormTest.test_custom_form_saves_many_to_many_field'])


def test_p2p_000():
    check(['auth_tests.test_forms.PasswordChangeFormTest.test_field_order', 'auth_tests.test_forms.PasswordChangeFormTest.test_html_autocomplete_attributes', 'auth_tests.test_forms.PasswordChangeFormTest.test_incorrect_password', 'auth_tests.test_forms.PasswordChangeFormTest.test_password_verification', 'auth_tests.test_forms.PasswordChangeFormTest.test_password_whitespace_not_stripped', 'auth_tests.test_forms.PasswordChangeFormTest.test_success', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_html_autocomplete_attributes', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_missing_passwords', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_non_matching_passwords', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_one_password', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_password_whitespace_not_stripped', 'auth_tests.test_forms.AdminPasswordChangeFormTest.test_success', 'auth_tests.test_forms.UserCreationFormTest.test_both_passwords', 'auth_tests.test_forms.UserCreationFormTest.test_custom_form', 'auth_tests.test_forms.UserCreationFormTest.test_custom_form_hidden_username_field', 'auth_tests.test_forms.UserCreationFormTest.test_custom_form_with_different_username_field', 'auth_tests.test_forms.UserCreationFormTest.test_duplicate_normalized_unicode', 'auth_tests.test_forms.UserCreationFormTest.test_html_autocomplete_attributes', 'auth_tests.test_forms.UserCreationFormTest.test_invalid_data', 'auth_tests.test_forms.UserCreationFormTest.test_normalize_username'])


def test_p2p_020():
    check(['auth_tests.test_forms.PasswordResetFormTest.test_preserve_username_case', 'auth_tests.test_forms.PasswordResetFormTest.test_save_html_email_template_name', 'auth_tests.test_forms.PasswordResetFormTest.test_save_plaintext_email', 'auth_tests.test_forms.PasswordResetFormTest.test_unusable_password', 'auth_tests.test_forms.PasswordResetFormTest.test_user_email_domain_unicode_collision', 'auth_tests.test_forms.PasswordResetFormTest.test_user_email_domain_unicode_collision_nonexistent', 'auth_tests.test_forms.PasswordResetFormTest.test_user_email_unicode_collision', 'auth_tests.test_forms.PasswordResetFormTest.test_user_email_unicode_collision_nonexistent', 'auth_tests.test_forms.UserChangeFormTest.test_bug_14242', 'auth_tests.test_forms.UserChangeFormTest.test_bug_17944_empty_password', 'auth_tests.test_forms.UserChangeFormTest.test_bug_17944_unknown_password_algorithm', 'auth_tests.test_forms.UserChangeFormTest.test_bug_17944_unmanageable_password', 'auth_tests.test_forms.UserChangeFormTest.test_bug_19133', 'auth_tests.test_forms.UserChangeFormTest.test_bug_19349_bound_password_field', 'auth_tests.test_forms.UserChangeFormTest.test_custom_form', 'auth_tests.test_forms.UserChangeFormTest.test_link_to_password_reset_in_helptext_via_to_field', 'auth_tests.test_forms.UserChangeFormTest.test_password_excluded', 'auth_tests.test_forms.UserChangeFormTest.test_unusable_password', 'auth_tests.test_forms.UserChangeFormTest.test_username_field_autocapitalize_none', 'auth_tests.test_forms.UserChangeFormTest.test_username_validity'])
