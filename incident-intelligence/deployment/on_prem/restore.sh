#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then printf 'Usage: %s BACKUP_DIRECTORY\n' "$0" >&2; exit 2; fi
backup_dir="$(realpath "$1")"
[[ -f "$backup_dir/SHA256SUMS" ]] || { echo "Incomplete backup" >&2; exit 1; }
(cd "$backup_dir" && sha256sum --check SHA256SUMS)
restore_work="$(mktemp -d)"
cleanup_restore() { rm -rf "$restore_work"; }
trap cleanup_restore EXIT
if [[ -f "$backup_dir/database.sql.age" && -f "$backup_dir/evidence.tar.gz.age" ]]; then
  command -v age >/dev/null || { echo "age is required for encrypted restore" >&2; exit 1; }
  age -d -o "$restore_work/database.sql" "$backup_dir/database.sql.age"
  age -d -o "$restore_work/evidence.tar.gz" "$backup_dir/evidence.tar.gz.age"
else
  [[ -f "$backup_dir/database.sql" && -f "$backup_dir/evidence.tar.gz" ]] || { echo "Incomplete backup" >&2; exit 1; }
  cp "$backup_dir/database.sql" "$restore_work/database.sql"
  cp "$backup_dir/evidence.tar.gz" "$restore_work/evidence.tar.gz"
fi
printf 'This replaces the current database and evidence volume. Type RESTORE to continue: '
read -r confirmation
[[ "$confirmation" == RESTORE ]] || { echo "Cancelled"; exit 1; }
echo "Stopping API and worker database clients."
docker compose stop api worker
restart_clients() { docker compose start api worker >/dev/null; }
restore_exit() { restart_clients; cleanup_restore; }
trap restore_exit EXIT
docker compose exec -T db dropdb -U "${POSTGRES_USER:-rfii}" --if-exists "${POSTGRES_DB:-incident_intelligence}"
docker compose exec -T db createdb -U "${POSTGRES_USER:-rfii}" "${POSTGRES_DB:-incident_intelligence}"
docker compose exec -T db psql -U "${POSTGRES_USER:-rfii}" "${POSTGRES_DB:-incident_intelligence}" <"$restore_work/database.sql"
docker compose run --rm --no-deps -T api tar -C /data -xzf - <"$restore_work/evidence.tar.gz"
docker compose start api worker
trap - EXIT
cleanup_restore
echo "Restore completed; run health checks and a report hash verification."
