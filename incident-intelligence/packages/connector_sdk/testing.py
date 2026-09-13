from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict, is_dataclass
import inspect
from typing import Any


@dataclass(frozen=True)
class ConnectorCertification:
    connector: str
    passed: bool
    checks: dict[str, bool]
    errors: tuple[str, ...]


def certify_connector(connector: Any, fixture: bytes) -> ConnectorCertification:
    """Run the mandatory read-only connector contract without external writes."""
    checks: dict[str, bool] = {}
    errors: list[str] = []
    metadata_value = getattr(connector, "metadata", {})
    metadata = asdict(metadata_value) if is_dataclass(metadata_value) else metadata_value
    checks["read_only_declaration"] = bool(metadata.get("read_only") is True)
    checks["version_metadata"] = bool(metadata.get("name") and metadata.get("version"))
    validator_name = "validate_configuration" if callable(getattr(connector, "validate_configuration", None)) else "validate_config"
    for method in (validator_name, "preview", "normalize", "health"):
        checks[f"method_{method}"] = callable(getattr(connector, method, None))
    public = {name.casefold() for name, _ in inspect.getmembers(connector) if not name.startswith("_")}
    checks["no_write_api"] = not bool(public & {"write", "update", "delete", "command", "dispatch", "publish"})
    try:
        if checks[f"method_{validator_name}"]:
            validator = getattr(connector, validator_name)
            validator({}) if validator_name == "validate_config" else validator()
        preview = connector.preview(fixture, {}) if checks["method_preview"] else None
        raw = {"payload": fixture.hex(), "provenance": {"fixture_sha256": __import__('hashlib').sha256(fixture).hexdigest()}}
        first = connector.normalize(raw) if checks["method_normalize"] else None
        second = connector.normalize(raw) if checks["method_normalize"] else None
        checks["preview"] = preview is not None
        checks["raw_preservation"] = fixture == bytes(fixture)
        checks["deterministic_normalization"] = first == second
        checks["provenance"] = bool(raw["provenance"])
        health = connector.health() if checks["method_health"] else None
        checks["health"] = bool(health and getattr(health, "status", health))
    except Exception as exc:
        errors.append(str(exc))
    passed = all(checks.values()) and not errors
    return ConnectorCertification(metadata.get("name", connector.__class__.__name__), passed, checks, tuple(errors))
