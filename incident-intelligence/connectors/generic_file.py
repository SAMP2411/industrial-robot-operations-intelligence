from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from packages.connector_sdk import ConnectorHealth, ConnectorMetadata, IngestionResult, PreviewResult, ValidationResult
from packages.ingestion_core import IngestionService


class GenericFileConnector:
    def __init__(self, *, session, filename: str, format_name: str):
        self.session = session
        self.filename = filename
        self.metadata = ConnectorMetadata(
            name=f"generic_{format_name}", version="1.0.0", source_type="historical_file",
            supported_formats=(format_name,), read_only=True, required_permissions=("read exported file",), maturity="validated",
        )

    def validate_configuration(self) -> ValidationResult:
        suffix = Path(self.filename).suffix.lower().lstrip(".")
        return ValidationResult(suffix in self.metadata.supported_formats, () if suffix in self.metadata.supported_formats else ("file format does not match connector",))

    def preview(self, content: bytes, mapping: dict) -> PreviewResult:
        with TemporaryDirectory() as directory:
            result = IngestionService(self.session, Path(directory)).preview(filename=self.filename, content=content, mapping=mapping)
        return PreviewResult(result.columns, result.sample_records, result.validation_errors)

    def ingest(self, content: bytes, mapping: dict) -> IngestionResult:
        raise RuntimeError("Use IngestionService.create_run and commit so raw evidence is preserved")

    def normalize(self, raw_record):
        return []

    def health(self) -> ConnectorHealth:
        validation = self.validate_configuration()
        return ConnectorHealth("healthy" if validation.valid else "invalid_configuration", {"read_only": True})

