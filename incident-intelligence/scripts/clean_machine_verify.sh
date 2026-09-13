#!/usr/bin/env bash
set -euo pipefail
required=(git docker "docker compose")
for command_name in "${required[@]}"; do
  if [[ "$command_name" == "docker compose" ]]; then docker compose version >/dev/null; else command -v "$command_name" >/dev/null; fi
done
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}" RFII_SECRET_KEY="${RFII_SECRET_KEY:?set RFII_SECRET_KEY}" docker compose config --quiet
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
trap 'docker compose down' EXIT
curl --fail --retry 20 --retry-delay 2 http://localhost:${RFII_PORT:-8000}/health
python3 scripts/validate_scorecard.py
python3 scripts/lint_product_claims.py
