from .conftest import seed_incident


def test_reviewer_role_exposes_approval_form(page, api):
    seeded = seed_incident(api, "report")
    page.evaluate("localStorage.rfiiRole='reviewer'")
    page.reload()
    page.get_by_role("button", name="Incidents").click()
    page.get_by_role("row").filter(has_text=seeded["incident"]["title"]).get_by_role("button", name="Investigate").click()
    page.get_by_role("tab", name="reports").click()
    assert page.get_by_role("heading", name="Reviewer approval").is_visible()
    assert page.locator("#report-form").is_hidden()
