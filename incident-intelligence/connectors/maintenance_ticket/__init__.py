from connectors.generic_file import GenericFileConnector


def connector(session, filename="maintenance_tickets.csv"):
    return GenericFileConnector(session=session, filename=filename, format_name=filename.rsplit(".", 1)[-1])

