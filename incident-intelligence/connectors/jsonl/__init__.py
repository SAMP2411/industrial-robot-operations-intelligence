from connectors.generic_file import GenericFileConnector


def connector(session, filename="export.jsonl"):
    return GenericFileConnector(session=session, filename=filename, format_name="jsonl")

