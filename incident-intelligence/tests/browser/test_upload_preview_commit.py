from pathlib import Path

from .conftest import seed_engagement


ROOT = Path(__file__).resolve().parents[2]


def test_upload_preview_preserve_and_commit(page, api):
    seeded = seed_engagement(api, "upload")
    source = api.post(
        f"/api/v1/diagnostic-engagements/{seeded['engagement']['id']}/sources",
        json={"name": "Robot events", "source_type": "robot_log"},
    ).json()
    page.get_by_role("button", name="Upload & preview").click()
    page.locator("#upload-engagement").select_option(seeded["engagement"]["id"])
    page.locator("#upload-engagement").dispatch_event("change")
    page.locator("#upload-source").select_option(source["id"])
    page.locator("#evidence-file").set_input_files(ROOT / "fixtures/malformed_sources/first_sprint_robot_events.csv")
    page.get_by_role("button", name="Preview—no import").click()
    page.wait_for_selector("text=Preview complete; review before preserving")
    page.get_by_role("button", name="Preserve file").click()
    page.wait_for_selector("text=explicit commit still required")
    page.get_by_role("button", name="Commit ingestion").click()
    page.wait_for_selector("text=Committed 3 raw records and 3 events", timeout=120_000)
    status = page.locator("#page-status").inner_text()
    assert "Committed 3 raw records and 3 events" in status, status
