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
    check(['template_tests.filter_tests.test_date.DateTests.test_date_lazy'])


def test_f2p_001():
    check(['i18n.tests.FormattingTests.test_get_format_lazy_format'])


def test_p2p_000():
    check(['i18n.tests.TestModels.test_lazy', 'i18n.tests.TestModels.test_safestr', 'i18n.tests.TestLanguageInfo.test_fallback_language_code', 'i18n.tests.TestLanguageInfo.test_localized_language_info', 'i18n.tests.TestLanguageInfo.test_unknown_language_code', 'i18n.tests.TestLanguageInfo.test_unknown_language_code_and_country_code', 'i18n.tests.TestLanguageInfo.test_unknown_only_country_code', 'i18n.tests.CountrySpecificLanguageTests.test_check_for_language', 'i18n.tests.CountrySpecificLanguageTests.test_check_for_language_null', 'i18n.tests.CountrySpecificLanguageTests.test_get_language_from_request', 'i18n.tests.CountrySpecificLanguageTests.test_get_language_from_request_null', 'i18n.tests.CountrySpecificLanguageTests.test_specific_language_codes', 'i18n.tests.TranslationFileChangedTests.test_ignores_non_mo_files', 'i18n.tests.TranslationFileChangedTests.test_resets_cache_with_mo_files', 'i18n.tests.DjangoFallbackResolutionOrderI18NTests.test_django_fallback', 'i18n.tests.UtilsTests.test_round_away_from_one', 'i18n.tests.TranslationFilesMissing.test_failure_finding_default_mo_files', 'i18n.tests.NonDjangoLanguageTests.test_check_for_language', 'i18n.tests.NonDjangoLanguageTests.test_non_django_language', 'i18n.tests.NonDjangoLanguageTests.test_plural_non_django_language'])


def test_p2p_020():
    check(['i18n.tests.FormattingTests.test_admin_javascript_supported_input_formats', 'i18n.tests.FormattingTests.test_all_format_strings', 'i18n.tests.FormattingTests.test_false_like_locale_formats', 'i18n.tests.FormattingTests.test_format_arbitrary_settings', 'i18n.tests.FormattingTests.test_get_custom_format', 'i18n.tests.FormattingTests.test_get_format_modules_lang', 'i18n.tests.FormattingTests.test_iter_format_modules', 'i18n.tests.FormattingTests.test_iter_format_modules_stability', 'i18n.tests.FormattingTests.test_l10n_disabled', 'i18n.tests.FormattingTests.test_l10n_enabled', 'i18n.tests.FormattingTests.test_locale_independent', 'i18n.tests.FormattingTests.test_localize_templatetag_and_filter', 'i18n.tests.FormattingTests.test_localized_as_text_as_hidden_input', 'i18n.tests.FormattingTests.test_localized_input', 'i18n.tests.FormattingTests.test_localized_input_func', 'i18n.tests.FormattingTests.test_localized_off_numbers', 'i18n.tests.FormattingTests.test_sanitize_separators', 'i18n.tests.FormattingTests.test_sanitize_strftime_format', 'i18n.tests.FormattingTests.test_sanitize_strftime_format_with_escaped_percent', 'i18n.tests.FormattingTests.test_sub_locales'])
