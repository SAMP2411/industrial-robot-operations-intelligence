def test_viewer_cannot_see_write_or_admin_forms(page):
    page.evaluate("localStorage.rfiiRole='viewer'")
    page.reload()
    page.get_by_role("button", name="Engagements").click()
    assert page.locator("#engagement-form").is_hidden()
    assert page.get_by_role("button", name="Admin").is_hidden()
