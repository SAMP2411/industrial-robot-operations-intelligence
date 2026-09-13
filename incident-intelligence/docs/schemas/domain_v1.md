# Domain schema v1

All primary identifiers are UUID strings and all domain rows carry `schema_version`, `created_at`, and `updated_at`. The Alembic `0001_initial_schema` migration creates the complete schema from the SQLAlchemy metadata.

Raw records preserve ingestion/source identity, filename/line, original timestamp, unmodified JSON payload, payload SHA-256, and ingestion time. Raw records reject update/delete through application sessions. Canonical events point to exactly one raw record and retain original/UTC time, time quality, clock offset, severity, system/asset mapping, message/state, unknown attributes, and normalizer version.

Evidence links bind an incident and optional hypothesis to one event, raw record, or report artifact using `supports`, `contradicts`, `contextual`, or `missing_expected`. Approved report artifacts carry version, format, SHA-256, reviewer/time, and an immutable flag.

The authoritative field definitions are in `packages/domain_models/models.py`; OpenAPI request/response shapes are available at `/openapi.json`.
