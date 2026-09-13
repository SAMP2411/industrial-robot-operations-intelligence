from connectors.generic_file import GenericFileConnector


def connector(session, filename="ros.log"):
    return GenericFileConnector(session=session, filename=filename, format_name="log")

