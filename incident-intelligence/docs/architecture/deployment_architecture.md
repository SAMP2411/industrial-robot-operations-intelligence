# Deployment architecture

## Local workstation

Local development may use SQLite and filesystem evidence storage:

```bash
make install
export RFII_DATABASE_URL=sqlite:///storage/incident_intelligence.db
make migrate
make run
```

## Single-customer on-prem pilot

Copy `.env.example` to `.env`, replace every placeholder secret, then run:

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
```

Services are PostgreSQL, API/UI, and a worker health boundary. Named volumes hold database and evidence state. The API applies Alembic migrations before serving. Put an HTTPS reverse proxy in front of port 8000 and restrict network access to approved analyst clients.

Create the initial administrator inside the API container using an interactive command:

```bash
docker compose exec api python tools/bootstrap_admin.py analyst@example.com
```

## Backup and restore

```bash
RFII_BACKUP_ROOT=/secure/backups ./deployment/on_prem/backup.sh
./deployment/on_prem/restore.sh /secure/backups/YYYYMMDDTHHMMSSZ
```

Backup emits a PostgreSQL dump, evidence archive, and SHA-256 manifest. Restore verifies hashes, requires the exact `RESTORE` confirmation, stops API/worker database clients, replaces database and evidence state, and restarts services. The procedure was exercised against the Compose deployment on 2026-07-19.
