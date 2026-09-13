# Phase 7: pilot readiness

Implemented six roles and permissions, scrypt password storage, expiring signed tokens, account disable/reset, append-only audits, upload controls, environment-only secrets, unprivileged container runtime, PostgreSQL Compose deployment, API/database/worker/storage health boundaries, and checksum-verified backup/restore.

Verification on 2026-07-19 built the images, started PostgreSQL/API/worker, migrated PostgreSQL to `0001_initial_schema`, passed API health/OpenAPI checks, created and verified a backup, restored it after quiescing API/worker connections, restarted services, and passed the post-restore health/migration checks. Containers were stopped afterward; named volumes were retained.
