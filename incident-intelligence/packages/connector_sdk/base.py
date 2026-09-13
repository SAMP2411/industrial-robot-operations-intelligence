from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreviewResult:
    columns: tuple[str, ...]
    sample_records: tuple[dict[str, Any], ...]
    errors: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class IngestionResult:
    summary: dict[str, int]


@dataclass(frozen=True)
class ConnectorHealth:
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectorMetadata:
    name: str
    version: str
    source_type: str
    supported_formats: tuple[str, ...]
    read_only: bool = True
    required_permissions: tuple[str, ...] = ("read",)
    schema_version: str = "1.0"
    vendor_status: str = "generic"
    maturity: str = "experimental"


class Connector(Protocol):
    metadata: ConnectorMetadata

    def validate_configuration(self) -> ValidationResult: ...
    def preview(self, content: bytes, mapping: dict[str, Any]) -> PreviewResult: ...
    def ingest(self, content: bytes, mapping: dict[str, Any]) -> IngestionResult: ...
    def normalize(self, raw_record: Any) -> list[Any]: ...
    def health(self) -> ConnectorHealth: ...

