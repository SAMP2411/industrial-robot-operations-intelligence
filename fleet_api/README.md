# FleetWatch Operator Console

FleetWatch is now the operator-facing layer for this robotics repo.

It started as a robot fleet observability MVP. In this repo, it has been advanced into a **local operator console** for the `Autonomous Factory Inspection Robot` benchmark:

- fleet telemetry remains available through optional InfluxDB-backed panels
- inspection artifacts from the ROS 2 benchmark can now be synced into SQLite
- findings can be acknowledged, assigned, reinspected, resolved, and closed
- missions can be reviewed and queued from a browser instead of opening raw JSON files manually

## Folder Layout

```text
fleet_api/
├── app/
│   ├── main.py
│   ├── storage.py
│   └── inspection_sync.py
├── docs/
│   └── STARTUP_PROJECT_SUMMARY.md
├── observability/
│   └── robot_fleet_dashboard.json
├── sim/
│   └── robot_sim.py
├── tests/
│   └── test_operator_console.py
├── ui/
│   └── Fleetwatch.html
├── .env.example
└── requirements.txt
```

## What This Service Does

### 1. Fleet observability

Optional InfluxDB-backed telemetry for:

- robot cards
- fault history
- fleet uptime
- battery/task summaries

### 2. Inspection operator workflow

SQLite-backed operator state for:

- sites
- assets
- missions
- evidence metadata
- findings
- finding events
- benchmark sync history

### 3. Operator actions

From the web UI or API, an operator can:

- sync the latest benchmark artifact set
- review imported findings
- preview evidence
- acknowledge a finding
- assign a finding
- request reinspection
- resolve a finding
- close a finding
- queue manual asset follow-up missions

## Run Locally

### 1. Install dependencies

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
python3 -m pip install --user --break-system-packages -r fleet_api/requirements.txt
```

### 2. Configure environment

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
cp fleet_api/.env.example fleet_api/.env
set -a
source fleet_api/.env
set +a
```

### 3. Start the operator API

From the repo root:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
set -a
source fleet_api/.env
set +a
uvicorn fleet_api.app.main:app --host 0.0.0.0 --port 8000
```

### 4. Open the UI

- UI: `http://localhost:8000/`
- OpenAPI docs: `http://localhost:8000/docs`

### 5. Sync the latest factory inspection run

1. Sign in with the demo user from `.env`.
2. Press `Sync latest benchmark`.
3. Review imported assets, findings, missions, and evidence.

## Optional: Start Fleet Telemetry Simulator

If you want the robot telemetry panels too:

1. Start InfluxDB 2.x and create the configured bucket.
2. Keep the same `.env` loaded.
3. Run:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
set -a
source fleet_api/.env
set +a
python3 fleet_api/sim/robot_sim.py
```

Then the same UI will show both:

- fleet observability
- inspection operations

## Developer Test Command

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
pytest fleet_api/tests/test_operator_console.py
```

## Important Current Reality

This is a strong local MVP, not a production SaaS.

Right now:

- the ROS runtime exports JSON/YAML/CSV/HTML files first
- FleetWatch syncs those artifacts into SQLite second
- operator-created missions are stored locally, not yet sent back into live robot execution

That is still a major step forward because the workflow no longer ends at raw files.
