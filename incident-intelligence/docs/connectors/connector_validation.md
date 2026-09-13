# Connector validation protocol

A connector is a read-only evidence adapter. It must never write to a robot, fleet manager, WMS/WCS/WES, PLC, network controller, or production system.

Certification requires: representative permitted fixtures; schema/profile version; provenance and immutable raw preservation; timestamp/timezone behavior; nested and missing-field cases; malformed-row behavior; idempotency; large-file behavior; retry behavior; and a passing connector contract suite. Record the fixture fingerprint and test command in the certification record.

Generic CSV, JSON, JSONL, structured-text, and safe ZIP paths are covered by automated tests. No named vendor export is certified until a permitted real export is registered with a non-sensitive fingerprint and its mapping profile passes these checks.
