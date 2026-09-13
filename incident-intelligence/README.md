# Robot Fleet Incident Intelligence

Robot Fleet Incident Intelligence is a read-only incident and reliability layer for brownfield warehouses and factories. It combines imperfect historical exports from robots, fleet software, WMS/WCS, PLCs, chargers, doors, lifts, network systems, and maintenance records; preserves the original evidence; reconstructs stoppages; measures downtime and recovery; makes uncertainty visible; and produces analyst-approved diagnostic and vendor-support packages.

The first commercial offer is a **Historical Robot Incident Diagnostic**, expected to be priced at €1,000–€3,000 per engagement. This is not a robot-control product, fleet manager, generic telemetry dashboard, or autonomous root-cause system.

## Start here

- Product overview: this README
- Complete feature and code flow: [`docs/SYSTEM_FEATURE_AND_CODE_FLOW.md`](docs/SYSTEM_FEATURE_AND_CODE_FLOW.md)
- Complete run-and-test guide: [`docs/RUN_AND_TEST_EVERY_FEATURE.md`](docs/RUN_AND_TEST_EVERY_FEATURE.md)
- Documentation index: [`docs/README.md`](docs/README.md)
- Current implementation status: [`docs/CURRENT_STATUS_FOR_PLAN_COMPARISON.md`](docs/CURRENT_STATUS_FOR_PLAN_COMPARISON.md)
- Legacy robotics demo: [`legacy/README.md`](legacy/README.md)

## What is implemented

- streamed CSV, JSON-array, JSONL, and structured-text preview/ingestion, nested field paths, encoding override, safe ZIP intake, and row-error download
- immutable raw records, SHA-256 file preservation, provenance, and idempotency keys
- versioned customer, site, system, asset, dependency, source, incident, and investigation models
- import adapter for the existing YAML asset registry
- UTC normalization, uncertainty intervals, evidence-backed clock alignment, event grouping, and analyst clock offsets
- filtered multi-source timelines, lifecycle markers, technical/business recovery, provenance-bearing metrics, dependency impact, and recurrence comparison
- versioned evidence-strength/independence policy, alternatives, contradiction gates, reviewer records, and explainable quality dimensions
- executive, technical, and vendor profiles generated as JSON, Markdown, HTML, PDF, CSV, and selected-evidence ZIPs from one structured snapshot
- immutable analyst-approved report versions, redaction audit, report comparison, and quality blockers
- browser forms for the complete analyst workflow with nine Playwright journeys
- tenant-scoped RBAC, OIDC-ready identity, rate limiting, append-only audit, optional AES-GCM evidence encryption, and independently approved deletion
- PostgreSQL/Alembic, SQLite development mode, durable jobs, TLS Docker Compose, JSON logs, Prometheus metrics/alerts, encrypted-backup option, security scans, SBOM/release automation, and restore tests
- three clearly labelled synthetic cross-system incident fixtures
- preserved ROS 2/Gazebo/Nav2 autonomy demo as an optional data generator

## Architecture

```text
Historical exports / mirrored read-only sources
                    ↓
          preview and explicit commit
                    ↓
       immutable raw evidence + hashes
                    ↓
      canonical events + asset mapping
                    ↓
      cross-system timeline reconstruction
                    ↓
 incident + downtime + recovery + data quality
                    ↓
 evidence-backed hypotheses + human review
                    ↓
 diagnostic report + selected vendor package
```

The active product lives in `apps/`, `packages/`, and `connectors/`. The older ROS/Gazebo/FleetWatch project is isolated under `legacy/autonomy_demo/`; the incident workflow has no ROS dependency.

## Quick start: local development

```bash
make install
cp .env.example .env
# For local SQLite development, set RFII_DATABASE_URL=sqlite:///storage/incident_intelligence.db
make migrate
make run
```

Open:

- incident console: <http://localhost:8000/>
- OpenAPI: <http://localhost:8000/docs>
- health: <http://localhost:8000/health>

For the first authenticated local administrator:

```bash
python3 tools/bootstrap_admin.py analyst@example.com
```

## Quick start: Docker Compose

Set strong `POSTGRES_PASSWORD` and `RFII_SECRET_KEY` values in `.env`, then:

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
```

See [deployment architecture](docs/architecture/deployment_architecture.md) for backup, restore, and on-prem notes.

## Test

```bash
python3 -m pytest
POSTGRES_PASSWORD=test RFII_SECRET_KEY=test-secret-at-least-32-bytes docker compose config --quiet
```

The inventory currently contains 99 tests across browser, unit/property, connector contract, integration, security, migration, performance/load, fault, backup/restore, and end-to-end scopes. The release gate also validates the scorecard, product claims, private-data boundary, and migration head.

## Simulated versus real

Everything under `fixtures/` is synthetic and is never evidence of market validation. The system is **validation-ready**, not commercially validated. The real-customer gates in `next.md` remain open until an operator dataset is analysed and reviewed and commercial/security objections are recorded.

The ROS/Gazebo benchmark is also simulated. It remains useful for engineering regression and export generation, but it is not the startup product.

## Autonomy demo

```bash
cd legacy/autonomy_demo/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-clean-cache \
  --packages-select factory_inspection_interfaces factory_inspection_mission
../tools/run_iteration_smoke_test.sh
```

The visual helper remains available at `legacy/autonomy_demo/tools/run_live_demo_stack.sh`. It starts the legacy FleetWatch autonomy console; it does not start the incident-intelligence product.

## Documentation

- [Current status for plan comparison](docs/CURRENT_STATUS_FOR_PLAN_COMPARISON.md)
- [Maximum-score implementation report](docs/phase_reports/max_score_phases_02_to_10.md)
- [Synthetic sample diagnostic](docs/sample_diagnostic/walkthrough.md)
- [Customer data request pack](docs/customer_data_pack/incident_data_request_checklist.md)
- [Customer security pack](docs/security/customer_security_pack/README.md)
- [Release checklist](docs/releases/release_checklist.md)
- [Documentation hub](docs/README.md)
- [Product definition](docs/product/product_definition.md)
- [Scope and non-goals](docs/product/scope_and_non_goals.md)
- [System architecture](docs/architecture/system_architecture.md)
- [Security architecture](docs/architecture/security_architecture.md)
- [Implementation roadmap and honest completion state](next.md)
- [Conversion phase reports](docs/phase_reports/phase_00_conversion_baseline.md)
