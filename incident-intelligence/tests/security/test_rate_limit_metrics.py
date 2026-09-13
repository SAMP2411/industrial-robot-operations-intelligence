from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def test_login_rate_limit_failed_audit_and_metrics(db_session, tmp_path):
    settings = Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test", login_attempt_limit=2)
    app = create_app(settings, initialize_schema=False)
    def session_override(): yield db_session
    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    client.post("/auth/users", headers={"X-Role": "admin"}, json={"email": "limit@example.test", "password": "correct-password", "role_name": "viewer"})
    for _ in range(2): assert client.post("/auth/token", json={"email": "limit@example.test", "password": "wrong-password"}).status_code == 401
    assert client.post("/auth/token", json={"email": "limit@example.test", "password": "wrong-password"}).status_code == 429
    metrics = client.get("/metrics", headers={"X-Role": "admin"})
    assert metrics.status_code == 200
    assert "rfii_login_failures_total" in metrics.text
    assert any(item["action"] == "login_failed" for item in client.get("/api/v1/audit", headers={"X-Role": "admin"}).json()["items"])
