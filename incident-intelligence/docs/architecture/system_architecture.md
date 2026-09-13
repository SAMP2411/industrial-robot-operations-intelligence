# System architecture

The product is a modular Python/FastAPI application with SQLAlchemy persistence and an optional synchronous report worker boundary. PostgreSQL is the pilot database; SQLite is supported for local tests. Alembic owns schema migration.

## Components

- `apps/diagnostic_api`: versioned CRUD, upload, timeline, investigation, report, authentication, audit, and validation APIs.
- `apps/operator_console`: incident-first read-only operational UI.
- `apps/report_worker`: deployable worker boundary; report generation is synchronous in the MVP.
- `packages/domain_models`: versioned relational model and mutation guards.
- `packages/ingestion_core`: preservation, format detection, preview, mapping, normalization, idempotency, and summaries.
- `packages/timeline_engine`: cross-source filtering, deterministic ordering, annotations, and analyst clock offsets.
- `packages/incident_engine`: downtime segments, recovery actions, and derived metrics.
- `packages/hypothesis_engine`: transparent evidence scoring and confidence caps.
- `packages/data_quality`: source coverage and issue assessment.
- `packages/report_generation`: structured reports, timeline export, evidence manifest, deterministic vendor ZIP, and immutable approval.
- `connectors`: read-only generic file connector contracts.
- `src`: preserved ROS autonomy benchmark, outside the startup runtime.

No incident-intelligence package imports ROS, Gazebo, or Nav2.
