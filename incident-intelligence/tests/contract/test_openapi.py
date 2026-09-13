from apps.diagnostic_api.main import app


def test_openapi_contains_historical_diagnostic_endpoints():
    schema = app.openapi()
    assert schema["info"]["title"] == "Robot Fleet Incident Intelligence API"
    for path in [
        "/api/v1/diagnostic-engagements",
        "/api/v1/sources/{source_id}/uploads/preview",
        "/api/v1/ingestion-runs/{run_id}/commit",
        "/api/v1/incidents/{incident_id}/timeline",
        "/api/v1/incidents/{incident_id}/reports",
    ]:
        assert path in schema["paths"]

