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
    check(['fixtures_regress.tests.TestFixtures.test_fixture_dirs_with_default_fixture_path'])


def test_f2p_001():
    check(['fixtures_regress.tests.TestFixtures.test_fixture_dirs_with_default_fixture_path_as_pathlib'])


def test_p2p_000():
    check(['fixtures_regress.tests.TestLoadFixtureFromOtherAppDirectory.test_fixtures_loaded', 'fixtures_regress.tests.NaturalKeyFixtureOnOtherDatabaseTests.test_natural_key_dependencies', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dependency_sorting_m2m_complex', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dependency_sorting_m2m_complex_circular_1', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dependency_sorting_m2m_complex_circular_2', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dependency_sorting_m2m_simple', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dependency_sorting_m2m_simple_circular', 'fixtures_regress.tests.M2MNaturalKeyFixtureTests.test_dump_and_load_m2m_simple', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_self_referential', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_2', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_3', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_4', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_5', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_6', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_dangling', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_long', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_normal', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_tight_circular', 'fixtures_regress.tests.NaturalKeyFixtureTests.test_dependency_sorting_tight_circular_2'])


def test_p2p_020():
    check(['fixtures_regress.tests.NaturalKeyFixtureTests.test_nk_deserialize', 'fixtures_regress.tests.TestFixtures.test_fixtures_dir_pathlib', 'fixtures_regress.tests.TestFixtures.test_invalid_data', 'fixtures_regress.tests.TestFixtures.test_invalid_data_no_ext', 'fixtures_regress.tests.TestFixtures.test_loaddata_forward_refs_split_fixtures', 'fixtures_regress.tests.TestFixtures.test_loaddata_no_fixture_specified', 'fixtures_regress.tests.TestFixtures.test_loaddata_not_found_fields_ignore', 'fixtures_regress.tests.TestFixtures.test_loaddata_not_found_fields_ignore_xml', 'fixtures_regress.tests.TestFixtures.test_loaddata_not_found_fields_not_ignore', 'fixtures_regress.tests.TestFixtures.test_loaddata_raises_error_when_fixture_has_invalid_foreign_key', 'fixtures_regress.tests.TestFixtures.test_loaddata_with_m2m_to_self', 'fixtures_regress.tests.TestFixtures.test_loaddata_with_valid_fixture_dirs', 'fixtures_regress.tests.TestFixtures.test_loaddata_works_when_fixture_has_forward_refs', 'fixtures_regress.tests.TestFixtures.test_path_containing_dots', 'fixtures_regress.tests.TestFixtures.test_pg_sequence_resetting_checks', 'fixtures_regress.tests.TestFixtures.test_proxy_model_included', 'fixtures_regress.tests.TestFixtures.test_relative_path', 'fixtures_regress.tests.TestFixtures.test_relative_path_in_fixture_dirs', 'fixtures_regress.tests.TestFixtures.test_ticket_20820', 'fixtures_regress.tests.TestFixtures.test_ticket_22421'])


def test_p2p_040():
    check(['fixtures_regress.tests.TestFixtures.test_unimportable_serializer', 'fixtures_regress.tests.TestFixtures.test_unknown_format'])
