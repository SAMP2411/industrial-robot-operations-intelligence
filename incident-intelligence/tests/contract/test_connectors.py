from connectors.generic_csv import connector


def test_generic_connector_declares_read_only_permissions(db_session):
    instance = connector(db_session)
    assert instance.metadata.read_only is True
    assert instance.metadata.schema_version == "1.0"
    assert instance.health().status == "healthy"
