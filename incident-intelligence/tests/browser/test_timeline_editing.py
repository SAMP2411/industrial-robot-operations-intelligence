from .conftest import seed_incident


def test_incident_opens_timeline_workspace(page, api):
    seeded = seed_incident(api, "timeline")
    page.get_by_role("button", name="Incidents").click()
    row = page.get_by_role("row").filter(has_text=seeded["incident"]["title"])
    row.get_by_role("button", name="Investigate").click()
    page.wait_for_selector("text=Chronological timeline")
    assert page.get_by_role("button", name="Save boundaries").is_visible()
    assert page.get_by_role("button", name="Recalculate").is_visible()
