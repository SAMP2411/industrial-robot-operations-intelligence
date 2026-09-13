from connectors.generic_file import GenericFileConnector


def connector(session, filename="export.json"):
    return GenericFileConnector(session=session, filename=filename, format_name="json")

