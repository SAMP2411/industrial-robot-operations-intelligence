# Customer security pack

## Architecture and data flow

The application is a read-only historical diagnostic system. Browsers submit exported evidence through TLS to the API. The API stages data in chunks, validates it, preserves the original by content hash, and creates normalized records only after explicit commit. A durable worker boundary supports retries. PostgreSQL stores domain metadata; a dedicated volume stores evidence and generated reports. See `docs/architecture/` and `docs/security/threat_model.md`.

## Access, isolation, and audit

OIDC is the intended customer identity interface. Roles separate viewer, analyst, reviewer, and administrator permissions. Server-side customer scoping is applied to reads and writes and covered by cross-tenant tests. Audit events record actor, action, entity, time, and relevant details and are append-only at the application boundary.

## Protection and lifecycle

TLS is supplied by the secure deployment overlay. Raw evidence can be AES-GCM encrypted with a deployment secret; database/volume encryption remains a hosting control. Upload limits, archive traversal/bomb defenses, MIME/extension controls, redaction previews, selected-evidence vendor packages, retention previews, independent deletion approval, and deletion receipts reduce exposure. Backup encryption is available through `age`; restoration must be drilled in the target environment.

## Operations

JSON request logs, health checks, Prometheus metrics, alert rules, dependency/static/secret/container scans, migration tests, and SBOM generation are defined in the repository and CI. Vulnerability handling, incident response, retention, and update policies are in `docs/security/`.

## Deployment questionnaire

Before use, record: hosting owner and region; network boundaries and allowed ports; identity provider and MFA policy; administrator list; secret manager; database/volume encryption; retention period; backup location/encryption/RPO/RTO; log destination/retention; vulnerability notification contacts; subprocessors; deletion approvers; incident contacts; and required penetration or customer review.

## Known limitations

No independent security assessment or customer acceptance is recorded yet. Local-header authentication is development-only. Host administrators remain trusted. External SIEM, key management, database encryption, availability targets, and disaster-recovery guarantees depend on the selected environment. This system does not control operational equipment.
