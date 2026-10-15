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
    check(['utils_tests.test_timesince.TZAwareTimesinceTests.test_depth'])


def test_f2p_001():
    check(['utils_tests.test_timesince.TZAwareTimesinceTests.test_depth_invalid'])


def test_f2p_002():
    check(['utils_tests.test_timesince.TimesinceTests.test_other_units'])


def test_f2p_003():
    check(['utils_tests.test_timesince.TZAwareTimesinceTests.test_thousand_years_ago'])


def test_p2p_000():
    check(['utils_tests.test_timesince.TimesinceTests.test_both_date_objects', 'utils_tests.test_timesince.TimesinceTests.test_date_objects', 'utils_tests.test_timesince.TimesinceTests.test_different_timezones', 'utils_tests.test_timesince.TimesinceTests.test_display_first_unit', 'utils_tests.test_timesince.TimesinceTests.test_display_second_before_first', 'utils_tests.test_timesince.TimesinceTests.test_equal_datetimes', 'utils_tests.test_timesince.TimesinceTests.test_ignore_microseconds_and_seconds', 'utils_tests.test_timesince.TZAwareTimesinceTests.test_leap_year', 'utils_tests.test_timesince.TZAwareTimesinceTests.test_leap_year_new_years_eve', 'utils_tests.test_timesince.TZAwareTimesinceTests.test_months_edge', 'utils_tests.test_timesince.TimesinceTests.test_multiple_units', 'utils_tests.test_timesince.TZAwareTimesinceTests.test_naive_datetime_with_tzinfo_attribute', 'utils_tests.test_timesince.TZAwareTimesinceTests.test_second_before_equal_first_humanize_time_strings', 'utils_tests.test_timesince.TimesinceTests.test_depth', 'utils_tests.test_timesince.TimesinceTests.test_depth_invalid', 'utils_tests.test_timesince.TimesinceTests.test_leap_year', 'utils_tests.test_timesince.TimesinceTests.test_leap_year_new_years_eve', 'utils_tests.test_timesince.TimesinceTests.test_months_edge', 'utils_tests.test_timesince.TimesinceTests.test_naive_datetime_with_tzinfo_attribute', 'utils_tests.test_timesince.TimesinceTests.test_second_before_equal_first_humanize_time_strings'])


def test_p2p_020():
    check(['utils_tests.test_timesince.TimesinceTests.test_thousand_years_ago'])
