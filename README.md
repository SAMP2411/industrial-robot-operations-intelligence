# Industrial Robot Operations Intelligence

An end-to-end industrial robotics platform that joins autonomous inspection, fleet operations, evidence review, and historical incident diagnostics in one repository. A ROS 2 robot patrol produces structured inspection evidence; FleetWatch imports those outputs into an operator workflow; the incident-intelligence service combines historical records from multiple industrial systems into auditable timelines, hypotheses, recovery metrics, and reports.

## Objective

The project closes the gap between robot autonomy and operational decision-making. Navigation alone does not tell a maintenance team what changed, which asset needs attention, what evidence supports a finding, or how an incident affected production. This system carries information from the simulated inspection point to an operator console and onward into a structured diagnostic workflow.

## Motivation

Industrial robot incidents rarely exist in one log. Relevant evidence can be spread across robots, fleet managers, warehouse-control systems, programmable controllers, chargers, doors, lifts, wireless infrastructure, ticket systems, and maintenance exports. At the same time, daily inspection findings need an accountable workflow rather than isolated images. The platform demonstrates a unified architecture for collecting evidence, preserving provenance, managing findings, reconstructing incidents, measuring downtime, and producing reviewable outputs without issuing control commands from the diagnostic service.

## System overview

```text
                  LIVE INSPECTION AND OPERATIONS

Site / asset / mission configuration
                 |
                 v
      Gazebo + ROS 2 + Nav2 patrol
                 |
                 v
Inspection results, evidence, reports, campaign state
                 |
                 v
 FleetWatch artifact synchronization
                 |
                 v
Operator review: acknowledge -> assign -> reinspect -> resolve -> close
                 |
                 +---- follow-up mission queue


                  HISTORICAL INCIDENT DIAGNOSTICS

Robot / WMS / WCS / PLC / network / maintenance exports
                 |
                 v
Safe preview -> explicit commit -> immutable raw records
                 |
                 v
Normalization -> asset mapping -> aligned cross-system timeline
                 |
                 v
Incident boundaries -> downtime / recovery -> dependency impact
                 |
                 v
Evidence-linked hypotheses -> analyst review -> approved reports
```

## Major capabilities

### Autonomous inspection

- ROS 2 Jazzy packages, custom messages, and C++ mission nodes
- Gazebo Harmonic warehouse simulation with offline assets
- Nav2 waypoint navigation and recovery behavior
- Configuration-driven sites, assets, checkpoints, robots, and inspection profiles
- Visual, thermal, acoustic, and gauge-style synthetic inspection modes
- Raw and annotated evidence images
- Health scores, anomaly labels, severities, confidence, and diagnostics
- Continue, follow-up, watchlist, and safety-hold mission decisions
- Seeded scenarios, retries, smoke tests, and multi-seed regressions

### FleetWatch operator workflow

- JWT authentication and tenant-scoped APIs
- Optional InfluxDB live telemetry panels
- SQLite persistence for sites, assets, missions, findings, evidence, events, and sync history
- Import of the latest ROS benchmark report, campaign state, and evidence
- Finding acknowledgement, assignment, reinspection, resolution, and closure
- Manual and finding-driven follow-up mission queue
- Evidence retrieval for primary, raw, and annotated files
- Fleet and inspection health summaries in one browser console
- Integration test covering synchronization and the finding lifecycle

### Incident intelligence

- CSV, JSON, JSONL, structured text, safe ZIP, ROS-log, Wi-Fi-log, ticket, and rosbag-export ingestion
- Preview-before-commit workflow, encoding control, nested field mappings, and row-error download
- SHA-256 source preservation, provenance, immutable raw records, and idempotency
- Customer, site, system, asset, dependency, source, engagement, and incident models
- UTC normalization, clock offsets, uncertainty windows, lifecycle markers, and event groups
- Technical recovery, business recovery, downtime, dependency impact, and recurring-incident comparison
- Evidence-linked hypotheses, contradictions, alternative explanations, confidence policy, and human review
- Data-quality scoring and missing-evidence tracking
- Executive, technical, and vendor outputs in JSON, Markdown, HTML, PDF, CSV, and ZIP
- RBAC, authentication, audit events, rate limiting, retention/deletion workflow, and optional evidence encryption
- SQLite development mode and PostgreSQL/Alembic production mode
- Docker Compose API, database, and report-worker services
- Metrics, alert rules, backup/restore scripts, release checks, and a broad automated test suite

## Technology stack

- ROS 2 Jazzy, Nav2, Gazebo Harmonic, RViz
- C++17, Python 3.11+, OpenCV, pluginlib, yaml-cpp
- FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic
- SQLite and PostgreSQL
- Optional InfluxDB 2.x
- HTML, CSS, and browser JavaScript
- Docker Compose, Caddy, and Prometheus-compatible metrics
- Pytest, property tests, contract tests, integration tests, fault tests, and browser tests

## Repository structure

```text
.
├── src/
│   ├── factory_inspection_interfaces/    # ROS messages
│   └── factory_inspection_mission/       # Mission code, launch, config, robot, world
├── tools/                                # Robotics cleanup, smoke, retry, regression, demo
├── fleet_api/
│   ├── app/                              # FleetWatch API, persistence, sync, dispatch queue
│   ├── ui/                               # Operator console
│   ├── sim/                              # Robot telemetry simulator
│   ├── observability/                    # Grafana definition
│   └── tests/                            # Operator workflow integration test
└── incident-intelligence/
    ├── apps/                             # Diagnostic API, console, report worker
    ├── packages/                         # Domain, ingestion, timeline, evidence, reports
    ├── connectors/                       # Source adapters
    ├── deployment/                       # Containers, migrations, monitoring, backup
    ├── fixtures/                         # Clearly labelled synthetic incident datasets
    ├── scripts/                          # Validation, release, privacy, and sample tooling
    └── tests/                            # Automated quality and security suite
```

## Prerequisites

For the full stack:

- Ubuntu 24.04
- ROS 2 Jazzy
- Nav2, TurtleBot 4 simulation, `ros_gz`, OpenCV, and yaml-cpp dependencies
- Python 3.11 or newer
- `colcon`, `rosdep`, and `jq`
- Docker with the Compose plugin for PostgreSQL deployment
- Optional InfluxDB 2.x for live robot telemetry

Install base tools and resolve ROS dependencies:

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-rosdep jq libyaml-cpp-dev
sudo rosdep init   # only when rosdep has not been initialized
rosdep update

git clone https://github.com/SAMP2411/industrial-robot-operations-intelligence.git
cd industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

## Part 1: build and run autonomous inspection

### Build the ROS workspace

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-clean-cache \
  --packages-select factory_inspection_interfaces factory_inspection_mission
source install/setup.bash
```

### Run a headless patrol

```bash
export FACTORY_SCENARIO_SEED=4242
ros2 launch factory_inspection_mission benchmark_patrol.launch.py \
  headless:=True use_rviz:=False
```

### Run with Gazebo and RViz

```bash
export FACTORY_SCENARIO_SEED=4242
ros2 launch factory_inspection_mission benchmark_patrol.launch.py \
  headless:=False use_rviz:=True
```

Outputs are created beneath `~/.ros/factory_inspection/benchmark/`. They include the latest report, campaign state, CSV history, browser dashboard, generated scenario, logs, and evidence images.

### Robotics smoke and regression tests

```bash
./tools/clean_benchmark_runtime.sh
FACTORY_SCENARIO_SEED=4242 ./tools/run_iteration_smoke_test.sh

FACTORY_SCENARIO_SEED=4242 \
FACTORY_BENCHMARK_SUCCESS_PATTERN='Round 1 summary:' \
FACTORY_BENCHMARK_TIMEOUT_SECONDS=240 \
./tools/run_benchmark_with_retry.sh headless:=True use_rviz:=False

./tools/run_benchmark_regression.sh 4242 5151 6262
```

Validate the generated report:

```bash
test -s ~/.ros/factory_inspection/benchmark/latest_report.json
jq . ~/.ros/factory_inspection/benchmark/latest_report.json
```

## Part 2: run FleetWatch and import inspection results

### Configure the Python environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r fleet_api/requirements.txt
cp fleet_api/.env.example fleet_api/.env
```

Edit `fleet_api/.env`. For inspection-only operation, SQLite is required and InfluxDB is optional. Keep these paths relative to the repository root:

```dotenv
FLEETWATCH_SQLITE_PATH=./fleet_api/data/fleetwatch.db
FACTORY_BENCHMARK_RUNTIME_ROOT=/home/your-user/.ros/factory_inspection/benchmark
FACTORY_SITE_CONFIG=./src/factory_inspection_mission/config/sites/benchmark_site.yaml
FACTORY_ASSET_REGISTRY=./src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml
FACTORY_INSPECTION_PROFILES=./src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml
```

Generate and set a strong `SECRET_KEY`. Set `DEMO_EMAIL` and `DEMO_PASSWORD` for an automatically created local account.

```bash
set -a
source fleet_api/.env
set +a
uvicorn fleet_api.app.main:app --host 0.0.0.0 --port 8000
```

Open:

- FleetWatch console: <http://localhost:8000/>
- OpenAPI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

After a ROS run completes, sign in and select **Sync latest benchmark**. The sync imports site/asset configuration, missions, findings, evidence, and events without modifying the source artifacts.

### FleetWatch workflow

1. Run or complete a benchmark patrol.
2. Start FleetWatch from the repository root with the environment loaded.
3. Sign in using the configured demo account or register an account.
4. Select **Sync latest benchmark**.
5. Open an imported finding and inspect its primary, raw, and annotated evidence.
6. Acknowledge and assign the finding.
7. Request reinspection to add a follow-up item to the operator mission queue.
8. Resolve and close the finding after review.
9. Inspect the event history for the recorded lifecycle transitions.

### FleetWatch API groups

- `/auth/*`: registration and tokens
- `/fleet/*` and `/ingest/*`: optional InfluxDB telemetry
- `/api/v1/operator/summary`: operator KPIs
- `/api/v1/sync/benchmark/latest`: artifact synchronization
- `/api/v1/sites` and `/api/v1/assets*`: inspection hierarchy
- `/api/v1/missions*`: mission creation, pause, and cancel
- `/api/v1/findings*`: query and lifecycle operations
- `/api/v1/evidence*`: evidence retrieval

### Test FleetWatch

```bash
source .venv/bin/activate
python -m pytest -q fleet_api/tests/test_operator_console.py
```

The integration test creates isolated temporary runtime data and verifies synchronization, summary counts, finding acknowledgement, assignment, reinspection, resolution, closure, mission creation, and evidence access.

## Part 3: run incident intelligence locally

The diagnostic service is read-only with respect to robots and industrial control systems. It imports files or mirrored data and does not expose mission dispatch, navigation, teleoperation, PLC-write, or robot-control routes.

### SQLite development setup

```bash
cd incident-intelligence
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
cp .env.example .env
```

Edit `.env` for local development:

```dotenv
RFII_DATABASE_URL=sqlite:///storage/incident_intelligence.db
RFII_STORAGE_ROOT=./storage
RFII_AUTH_REQUIRED=true
RFII_SECRET_KEY=replace-with-at-least-32-random-bytes
RFII_CORS_ORIGINS=http://localhost:8100
RFII_APP_ENV=development
```

Load the environment, migrate, and create the first administrator:

```bash
set -a
source .env
set +a
alembic upgrade head
python tools/bootstrap_admin.py analyst@example.com
```

The bootstrap tool securely prompts for a password of at least 12 characters.

Start the service on port 8100 so it can run alongside FleetWatch:

```bash
uvicorn apps.diagnostic_api.main:app --host 0.0.0.0 --port 8100
```

Open:

- Diagnostic console: <http://localhost:8100/>
- OpenAPI: <http://localhost:8100/docs>
- Health: <http://localhost:8100/health>

### Core diagnostic workflow

1. Authenticate and create a customer.
2. Create a site and the relevant systems/assets, or import an asset registry.
3. Create a diagnostic engagement and one or more data sources.
4. Upload a supported file and preview parsing/mapping results.
5. Correct mappings or encoding issues, then explicitly commit ingestion.
6. Create an incident and set timeline boundaries.
7. Review normalized events, uncertainty, clock alignment, and event groups.
8. Record downtime segments, lifecycle markers, recovery actions, and milestones.
9. Add hypotheses and link supporting, contradicting, contextual, or missing evidence.
10. Recalculate data quality and complete independent human reviews.
11. Generate executive, technical, or vendor report profiles.
12. Preview redaction, approve an immutable report version, and export the artifact.

Interactive OpenAPI at `/docs` exposes the exact schemas for all endpoints.

## Part 4: run incident intelligence with Docker Compose

From `incident-intelligence/`:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set unique values for `POSTGRES_PASSWORD` and `RFII_SECRET_KEY`, then:

```bash
docker compose up --build -d
docker compose ps
curl -fsS http://localhost:8000/health
docker compose logs -f api worker
```

The default Compose stack contains PostgreSQL 16, the API, and a durable report worker. Persistent volumes hold database and evidence data.

Stop the stack without deleting volumes:

```bash
docker compose down
```

## Complete incident-intelligence test procedure

Run from `incident-intelligence/` with its virtual environment active.

### Full automated suite

```bash
python -m pytest
```

The suite covers unit, property, parser fuzz, connector contract, API contract, integration, end-to-end workflow, authentication, tenant isolation, encryption, uploads, retention, migrations, fault handling, performance, browser behavior, release invariants, backup/restore, and report packaging. PostgreSQL-specific tests may skip when no PostgreSQL test database is configured.

### Docker configuration validation

```bash
POSTGRES_PASSWORD=test-password \
RFII_SECRET_KEY=test-secret-at-least-32-bytes \
docker compose config --quiet
```

### Privacy boundary scan

```bash
python scripts/scan_private_data.py
```

### Connector validation

```bash
python scripts/validate_connector.py --help
```

Use the displayed arguments to validate a connector against an isolated sample before enabling it for an engagement.

### Release gate

```bash
python scripts/release_gate.py
```

The release gate checks required artifacts, scorecard data, product claims, the private-data boundary, the Alembic migration head, and the automated tests.

## Running all three subsystems together

Use separate terminals:

1. ROS/Gazebo inspection from the repository root.
2. FleetWatch on port 8000 from the repository root.
3. Incident intelligence on port 8100 from `incident-intelligence/`.

Example:

```bash
# Terminal 1
source /opt/ros/jazzy/setup.bash
source install/setup.bash
FACTORY_SCENARIO_SEED=4242 \
ros2 launch factory_inspection_mission benchmark_patrol.launch.py \
  headless:=True use_rviz:=False

# Terminal 2
source .venv/bin/activate
set -a; source fleet_api/.env; set +a
uvicorn fleet_api.app.main:app --port 8000

# Terminal 3
cd incident-intelligence
source .venv/bin/activate
set -a; source .env; set +a
uvicorn apps.diagnostic_api.main:app --port 8100
```

Verify:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8100/health
test -s ~/.ros/factory_inspection/benchmark/latest_report.json
```

## Data and persistence

- ROS benchmark outputs: `~/.ros/factory_inspection/benchmark/`
- Operator mission queue: `~/.ros/factory_inspection/operator/operator_mission_queue.yaml`
- FleetWatch SQLite database: configured by `FLEETWATCH_SQLITE_PATH`
- Incident evidence and local state: configured by `RFII_STORAGE_ROOT`
- Incident database: configured by `RFII_DATABASE_URL`
- Docker database/evidence: named Compose volumes

Local databases, secrets, uploads, generated reports, caches, ROS build outputs, and private customer data are excluded from version control.

## Security model

- Fleet and inspection APIs are tenant scoped.
- Telemetry ingestion uses a separate key from operator authentication.
- Incident permissions distinguish read, write, upload, approval, and administration.
- Raw evidence retains hashes and provenance.
- Optional AES-GCM evidence encryption protects stored material.
- Upload handling enforces type/size/path safety constraints.
- Audit events cover sensitive workflow transitions.
- Report approval creates immutable versions.
- Data deletion uses preview, independent approval, and execution stages.
- Production deployment should use TLS, externally managed secrets, database backups, least-privilege identities, retention policies, and restricted network access.

## Troubleshooting

### Robotics

- Source `/opt/ros/jazzy/setup.bash` and `install/setup.bash` in each terminal.
- Run `./tools/clean_benchmark_runtime.sh` before retrying stale Gazebo/Nav2 launches.
- Inspect the newest retry log under `~/.ros/factory_inspection/benchmark/retry_logs/`.
- Use `headless:=True use_rviz:=False` to isolate graphical failures.

### FleetWatch

- Start Uvicorn from the repository root so relative configuration paths resolve correctly.
- Confirm `FACTORY_BENCHMARK_RUNTIME_ROOT` contains `latest_report.json` before synchronization.
- A degraded `/health` result normally means optional InfluxDB is unavailable; the SQLite inspection workflow can still be checked through `/api/v1/health`.
- Ensure `DEMO_*` values are loaded before process startup.

### Incident intelligence

- Run commands from `incident-intelligence/` so Alembic and package imports resolve correctly.
- Confirm the storage directory is writable.
- Run `alembic upgrade head` after changing database instances or pulling migrations.
- Use a PostgreSQL URL with `postgresql+psycopg://` and install the `postgres` optional dependency for production.
- If authentication is enabled, create the administrator after exporting the same database and secret configuration used by the API.

## Scope and boundaries

The autonomous inspection environment and bundled incident fixtures are simulations intended for engineering validation. The incident service is not a robot-control product and intentionally does not command equipment. The platform must be integrated with real robot drivers, validated data contracts, site safety controls, organizational security policies, and qualified human review before industrial deployment.
