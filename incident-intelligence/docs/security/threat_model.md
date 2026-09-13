# Threat model

## Scope and assets

The protected assets are uploaded operational evidence, normalized records, diagnostic conclusions, user identities, audit history, report packages, encryption keys, and backups. The trust boundaries are browser-to-proxy, proxy-to-API, API-to-database/storage, worker-to-storage/database, administrator-to-host, and backup export.

## STRIDE review

| Threat | Principal controls | Residual risk |
|---|---|---|
| Spoofing | OIDC-ready identity boundary, local-header mode limited to development, role permissions, login throttling | Identity-provider configuration is deployment-owned |
| Tampering | SHA-256 preservation, atomic writes, immutable raw/audit/report guards, migration tests | A fully privileged host administrator remains trusted |
| Repudiation | Actor-attributed append-only audit events, report hashes, deletion receipts | External log retention requires deployment integration |
| Information disclosure | Tenant scoping, least-privilege roles, redaction, optional AES-GCM evidence encryption, TLS proxy | Metadata/database encryption depends on host or managed database controls |
| Denial of service | Upload limits, ZIP bomb checks, chunked staging, durable retry jobs, rate limiting, health/metrics | Capacity must be sized and monitored for each pilot |
| Elevation of privilege | Central authorization dependencies and cross-tenant security tests | Independent security review is still pending |

## Review triggers

Repeat this review after a new connector type, identity provider, hosting topology, customer-facing integration, encryption design, or cross-tenant data path is introduced. Use `docs/validation/external_security_review.md` for independent findings and closure evidence.
