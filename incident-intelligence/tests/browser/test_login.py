def test_console_loads_in_local_analyst_mode(page):
    assert page.get_by_role("heading", name="Overview").is_visible()
    assert "Role: analyst" in page.locator("#identity").inner_text()
    assert page.get_by_role("button", name="Sign in").is_visible()
