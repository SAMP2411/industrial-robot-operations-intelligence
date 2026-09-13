# Inspection + Operator Dashboard Fusion

This is the complete combined project. The ROS inspection system produces benchmark artifacts; FleetWatch imports those artifacts into an operator workflow; the included incident-intelligence service provides the newer read-only, multi-source diagnostic and reporting product.

## End-to-end flow

```text
ROS 2/Nav2 patrol -> waypoint inspections -> evidence and reports
        -> FleetWatch SQLite sync -> review/actions/reinspection queue
        -> optional incident-intelligence ingestion and diagnostics
```

## Capabilities

The root ROS workspace provides simulation, navigation, configurable inspections, evidence capture, anomaly reporting, mission decisions, multi-platform support, and structured JSON/CSV/Markdown/HTML output.

`fleet_api/` adds:

- optional InfluxDB fleet telemetry and robot/fault/uptime panels
- JWT login and tenant-scoped APIs
- SQLite persistence for sites, assets, missions, evidence, findings, events, and sync history
- finding acknowledgement, assignment, reinspection, resolution, and closure
- operator-created follow-up mission queue
- browser console, API, simulator, and integration tests

`incident-intelligence/` adds the later OnPoint/RFII functionality:

- CSV, JSON, JSONL, text, ZIP, ROS-log, Wi-Fi-log, ticket, and rosbag-export connectors
- immutable evidence/provenance, normalization, asset mapping, timelines, recovery/downtime metrics, hypotheses, contradictions, and data-quality scoring
- analyst review and executive/technical/vendor reports in JSON, Markdown, HTML, PDF, CSV, and ZIP formats
- RBAC/OIDC readiness, audit, rate limiting, retention/deletion controls, optional encryption, PostgreSQL/Alembic and SQLite modes
- Docker/on-prem deployment, observability, backup/restore, security/release automation, fixtures, and broad automated tests

## Run the integrated inspection and console

Requires ROS 2 Jazzy/Nav2/Gazebo plus Python 3.10+.

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-clean-cache \
  --packages-select factory_inspection_interfaces factory_inspection_mission
source install/setup.bash
./tools/run_iteration_smoke_test.sh

python3 -m venv .venv
source .venv/bin/activate
pip install -r fleet_api/requirements.txt
cp fleet_api/.env.example fleet_api/.env
# Configure secrets; relative project paths in the example work from this root.
set -a; source fleet_api/.env; set +a
uvicorn fleet_api.app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/`, sign in, and use **Sync latest benchmark** after a ROS run. Test the console with `pytest fleet_api/tests/test_operator_console.py`.

## Run incident intelligence

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# For local development set RFII_DATABASE_URL=sqlite:///storage/incident_intelligence.db
make migrate
make run
```

Open `http://localhost:8000/`; consult `incident-intelligence/docs/RUN_AND_TEST_EVERY_FEATURE.md` and `incident-intelligence/docs/SYSTEM_FEATURE_AND_CODE_FLOW.md` for its complete workflow. Run `python3 -m pytest` from that subdirectory for its test inventory.

The two web services both default to port 8000, so assign different ports if running them simultaneously.

## Layout and provenance

- `src/`, `tools/`, and `docs/` came from `/home/samarth/inspection-with-fleetapi`
- `fleet_api/` is the enhanced dashboard from that same fused repository
- `incident-intelligence/` is the active product from `/home/samarth/onpoint-monitoring-startup`; its duplicate legacy robotics subtree was omitted because the newer direct fusion is already present at this project's root

All original source folders remain unchanged. Generated builds/logs/caches, local databases, virtual environments, private data, secrets, runtime report/upload state, and nested Git metadata were excluded and will be recreated by normal setup and execution.
