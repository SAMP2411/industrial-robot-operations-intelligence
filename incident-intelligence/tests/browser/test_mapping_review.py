from .conftest import seed_engagement


def test_mapping_review_records_rationale(page, api):
    seeded = seed_engagement(api, "mapping")
    asset = api.post("/api/v1/assets", json={"site_id": seeded["site"]["id"], "name": "AMR 7", "asset_type": "amr"}).json()
    page.get_by_role("button", name="Mapping review").click()
    page.locator("#mapping-engagement").select_option(seeded["engagement"]["id"])
    page.locator("#external-identifier").fill("RBT-007")
    page.locator("#mapping-asset").select_option(asset["id"])
    page.locator("#mapping-rationale").fill("Confirmed against the supplied site register")
    page.get_by_role("button", name="Save audited decision").click()
    page.wait_for_selector("text=Mapping decision saved and audited")
