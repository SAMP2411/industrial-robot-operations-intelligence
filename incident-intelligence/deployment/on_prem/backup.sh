#!/usr/bin/env bash
set -euo pipefail
backup_root="${RFII_BACKUP_ROOT:-./backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="$backup_root/$timestamp"
mkdir -p "$destination"
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-rfii}" "${POSTGRES_DB:-incident_intelligence}" >"$destination/database.sql"
docker compose run --rm --no-deps -T api tar -C /data -czf - uploads reports >"$destination/evidence.tar.gz"
(cd "$destination" && sha256sum database.sql evidence.tar.gz >SHA256SUMS)
if [[ -n "${RFII_BACKUP_AGE_RECIPIENT:-}" ]]; then
  command -v age >/dev/null || { echo "age is required for encrypted backup" >&2; exit 1; }
  age -r "$RFII_BACKUP_AGE_RECIPIENT" -o "$destination/database.sql.age" "$destination/database.sql"
  age -r "$RFII_BACKUP_AGE_RECIPIENT" -o "$destination/evidence.tar.gz.age" "$destination/evidence.tar.gz"
  rm "$destination/database.sql" "$destination/evidence.tar.gz"
  (cd "$destination" && sha256sum database.sql.age evidence.tar.gz.age >SHA256SUMS)
fi
printf 'Backup written to %s\n' "$destination"
