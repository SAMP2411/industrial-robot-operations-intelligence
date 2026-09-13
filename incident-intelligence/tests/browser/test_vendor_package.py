from .conftest import seed_incident


def test_vendor_package_requires_explicit_selection(page, api):
    seeded = seed_incident(api, "vendor")
    page.get_by_role("button", name="Incidents").click()
    page.get_by_role("row").filter(has_text=seeded["incident"]["title"]).get_by_role("button", name="Investigate").click()
    page.get_by_role("tab", name="reports").click()
    assert page.get_by_label("Explicit raw-record selection").is_visible()
    assert page.get_by_label("Inclusion reason").input_value()
