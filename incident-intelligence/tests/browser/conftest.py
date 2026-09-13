from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
CHROME = Path(os.getenv("CHROME_BIN", "/usr/bin/google-chrome"))


def _free_port() -> int:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    port = _free_port()
    state = tmp_path_factory.mktemp("browser-state")
    env = {
        **os.environ,
        "RFII_DATABASE_URL": f"sqlite:///{state / 'browser.db'}",
        "RFII_STORAGE_ROOT": str(state / "storage"),
        "RFII_AUTH_REQUIRED": "false",
        "PYTHONPATH": str(ROOT),
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.diagnostic_api.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        # Cold SQLite schema creation can take over two minutes on constrained CI hosts.
        startup_deadline = time.monotonic() + 180
        while time.monotonic() < startup_deadline:
            if process.poll() is not None:
                raise RuntimeError(process.stderr.read())
            try:
                if httpx.get(f"{base_url}/health", timeout=.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(.05)
        else:
            raise RuntimeError("browser test server did not start")
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture
def page(live_server):
    if not CHROME.exists():
        pytest.skip(f"Chrome executable not found at {CHROME}")
    with sync_playwright() as manager:
        browser = manager.chromium.launch(executable_path=str(CHROME), headless=True, args=["--no-sandbox"])
        context = browser.new_context(base_url=live_server)
        page = context.new_page()
        page.goto("/")
        page.wait_for_selector("#content h2")
        yield page
        context.close()
        browser.close()


@pytest.fixture
def api(live_server):
    with httpx.Client(base_url=live_server, headers={"X-Role": "analyst", "X-Actor": "browser-fixture"}) as client:
        yield client


def seed_engagement(api: httpx.Client, suffix: str = "browser") -> dict:
    customer = api.post("/api/v1/customers", json={"name": f"Customer {suffix}"}).json()
    site = api.post("/api/v1/sites", json={"customer_id": customer["id"], "name": f"Site {suffix}", "timezone": "UTC"}).json()
    engagement = api.post(
        "/api/v1/diagnostic-engagements",
        json={"customer_id": customer["id"], "site_id": site["id"], "title": f"Diagnostic {suffix}"},
    ).json()
    return {"customer": customer, "site": site, "engagement": engagement}


def seed_incident(api: httpx.Client, suffix: str = "browser") -> dict:
    records = seed_engagement(api, suffix)
    incident = api.post(
        "/api/v1/incidents",
        json={
            "diagnostic_engagement_id": records["engagement"]["id"],
            "site_id": records["site"]["id"],
            "title": f"Incident {suffix}",
            "started_at": "2026-07-19T08:00:00Z",
            "recovered_at": "2026-07-19T08:10:00Z",
            "business_impact": "One workflow delayed",
        },
    ).json()
    return {**records, "incident": incident}
