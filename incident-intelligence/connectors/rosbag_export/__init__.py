from connectors.generic_file import GenericFileConnector


def connector(session, filename="rosbag-neutral-events.jsonl"):
    return GenericFileConnector(session=session, filename=filename, format_name="jsonl")

