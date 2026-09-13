from connectors.generic_file import GenericFileConnector
from packages.connector_sdk.testing import certify_connector


def test_generic_connector_passes_read_only_certification(db_session):
    connector = GenericFileConnector(session=db_session, filename="events.csv", format_name="csv")
    fixture = b"event_time,event_code\n2026-01-01T00:00:00Z,DOOR_OPEN\n"
    result = certify_connector(connector, fixture)
    assert result.passed, result
