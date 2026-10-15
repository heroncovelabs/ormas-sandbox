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
    check(['sitemaps_tests.test_http.HTTPSitemapTests.test_callable_sitemod_no_items'])


def test_p2p_000():
    check(['sitemaps_tests.test_http.DeprecatedTests.test_simple_sitemap_custom_index', 'sitemaps_tests.test_http.HTTPSitemapTests.test_simple_sitemap_custom_lastmod_index', 'sitemaps_tests.test_http.DeprecatedTests.test_simple_sitemap_custom_index_warning', 'sitemaps_tests.test_http.HTTPSitemapTests.test_alternate_i18n_sitemap_index', 'sitemaps_tests.test_http.HTTPSitemapTests.test_alternate_i18n_sitemap_limited', 'sitemaps_tests.test_http.HTTPSitemapTests.test_alternate_i18n_sitemap_xdefault', 'sitemaps_tests.test_http.HTTPSitemapTests.test_cached_sitemap_index', 'sitemaps_tests.test_http.HTTPSitemapTests.test_callable_sitemod_full', 'sitemaps_tests.test_http.HTTPSitemapTests.test_callable_sitemod_partial', 'sitemaps_tests.test_http.HTTPSitemapTests.test_empty_page', 'sitemaps_tests.test_http.HTTPSitemapTests.test_empty_sitemap', 'sitemaps_tests.test_http.HTTPSitemapTests.test_localized_priority', 'sitemaps_tests.test_http.HTTPSitemapTests.test_no_section', 'sitemaps_tests.test_http.HTTPSitemapTests.test_page_not_int', 'sitemaps_tests.test_http.HTTPSitemapTests.test_paged_sitemap', 'sitemaps_tests.test_http.HTTPSitemapTests.test_requestsite_sitemap', 'sitemaps_tests.test_http.HTTPSitemapTests.test_simple_custom_sitemap', 'sitemaps_tests.test_http.HTTPSitemapTests.test_simple_i18n_sitemap_index', 'sitemaps_tests.test_http.HTTPSitemapTests.test_simple_sitemap', 'sitemaps_tests.test_http.HTTPSitemapTests.test_simple_sitemap_index'])


def test_p2p_020():
    check(['sitemaps_tests.test_http.HTTPSitemapTests.test_simple_sitemap_section', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_get_latest_lastmod', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_get_latest_lastmod_none', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_get_urls_no_site_1', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_get_urls_no_site_2', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_item', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_last_modified', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_last_modified_date', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_last_modified_missing', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_last_modified_mixed', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_last_modified_tz', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_latest_lastmod_timezone', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_not_callable', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemap_without_entries', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemaps_lastmod_ascending', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemaps_lastmod_descending', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemaps_lastmod_mixed_ascending_last_modified_missing', 'sitemaps_tests.test_http.HTTPSitemapTests.test_sitemaps_lastmod_mixed_descending_last_modified_missing', 'sitemaps_tests.test_http.HTTPSitemapTests.test_x_robots_sitemap'])
