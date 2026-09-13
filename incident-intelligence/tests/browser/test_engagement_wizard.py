def test_engagement_wizard_creates_customer_site_and_engagement(page):
    page.get_by_role("button", name="Engagements").click()
    page.locator("#customer-name").fill("Browser Wizard Customer")
    page.locator("#site-name").fill("Browser Warehouse")
    page.locator("#engagement-title").fill("Browser door diagnostic")
    page.locator("#incident-window").fill("2026-07-19 08:00–09:00 UTC")
    page.locator("#permission-confirmed").check()
    page.get_by_role("button", name="Review and create").click()
    page.wait_for_selector("h2:text('Upload and preview workspace')")
    assert page.locator("#upload-engagement option").filter(has_text="Browser door diagnostic").count() == 1
