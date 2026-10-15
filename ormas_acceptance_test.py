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
    check(['admin_views.tests.ReadonlyTest.test_readonly_foreignkey_links_custom_admin_site'])


def test_p2p_000():
    check(['admin_views.tests.GetFormsetsWithInlinesArgumentTest.test_explicitly_provided_pk', 'admin_views.tests.GetFormsetsWithInlinesArgumentTest.test_implicitly_generated_pk', 'admin_views.tests.AdminCustomSaveRelatedTests.test_should_be_able_to_edit_related_objects_on_add_view', 'admin_views.tests.AdminCustomSaveRelatedTests.test_should_be_able_to_edit_related_objects_on_change_view', 'admin_views.tests.AdminCustomSaveRelatedTests.test_should_be_able_to_edit_related_objects_on_changelist_view', 'admin_views.tests.AdminViewsNoUrlTest.test_no_standard_modeladmin_urls', 'admin_views.tests.LimitChoicesToInAdminTest.test_limit_choices_to_as_callable', 'admin_views.tests.ValidXHTMLTests.test_lang_name_present', 'admin_views.tests.AdminViewUnicodeTest.test_unicode_delete', 'admin_views.tests.AdminViewUnicodeTest.test_unicode_edit', 'admin_views.tests.TestInlineNotEditable.test_GET_parent_add', 'admin_views.tests.SecureViewTests.test_secure_view_shows_login_if_not_logged_in', 'admin_views.tests.SecureViewTests.test_staff_member_required_decorator_works_with_argument', 'admin_views.tests.TestGenericRelations.test_generic_content_object_in_list_display', 'admin_views.tests.AdminInheritedInlinesTest.test_inline', 'admin_views.tests.AdminViewLogoutTests.test_client_logout_url_can_be_used_to_login', 'admin_views.tests.AdminViewLogoutTests.test_logout', 'admin_views.tests.TestCustomChangeList.test_custom_changelist', 'admin_views.tests.AdminViewFormUrlTest.test_change_form_URL_has_correct_value', 'admin_views.tests.AdminViewFormUrlTest.test_initial_data_can_be_overridden'])


def test_p2p_020():
    check(['admin_views.tests.AdminViewBasicTest.test_incorrect_lookup_parameters', 'admin_views.tests.AdminViewBasicTest.test_invalid_appindex_url', 'admin_views.tests.AdminViewBasicTest.test_isnull_lookups', 'admin_views.tests.AdminViewBasicTest.test_jsi18n_format_fallback', 'admin_views.tests.AdminViewBasicTest.test_jsi18n_with_context', 'admin_views.tests.AdminViewBasicTest.test_limited_filter', 'admin_views.tests.AdminViewBasicTest.test_logout_and_password_change_URLs', 'admin_views.tests.AdminViewBasicTest.test_multiple_sort_same_field', 'admin_views.tests.AdminViewBasicTest.test_named_group_field_choices_change_list', 'admin_views.tests.AdminViewBasicTest.test_named_group_field_choices_filter', 'admin_views.tests.AdminViewBasicTest.test_popup_add_POST', 'admin_views.tests.AdminViewBasicTest.test_popup_dismiss_related', 'admin_views.tests.AdminViewBasicTest.test_relation_spanning_filters', 'admin_views.tests.AdminViewBasicTest.test_render_views_no_subtitle', 'admin_views.tests.AdminViewBasicTest.test_resolve_admin_views', 'admin_views.tests.AdminViewBasicTest.test_sort_indicators_admin_order', 'admin_views.tests.AdminViewBasicTest.test_sortable_by_columns_subset', 'admin_views.tests.AdminViewBasicTest.test_sortable_by_no_column', 'admin_views.tests.AdminViewBasicTest.test_trailing_slash_required', 'admin_views.tests.AdminViewBasicTest.test_view_subtitle_per_object'])
