from .conftest import seed_incident


def test_hypothesis_studio_creates_alternative(page, api):
    seeded = seed_incident(api, "hypothesis")
    page.get_by_role("button", name="Incidents").click()
    page.get_by_role("row").filter(has_text=seeded["incident"]["title"]).get_by_role("button", name="Investigate").click()
    page.get_by_role("tab", name="hypotheses").click()
    page.locator("#hyp-title").fill("Door controller was unavailable")
    page.locator("#hyp-description").fill("Alternative explanation to compare with network delay")
    page.get_by_role("button", name="Create hypothesis").click()
    page.get_by_role("cell", name="Door controller was unavailable").wait_for()
