# Maximum-score implementation report: phases 2–10

**Status date:** 2026-07-19

**Scope:** repository-controlled implementation and automated evidence only

## Phase 2 — analyst console

Implemented a browser-only engagement, upload, mapping, incident/timeline, clock, downtime/recovery, hypothesis/evidence, quality, report approval, vendor selection, role, administration, and validation workflow. Nine named Playwright journeys and role checks pass. A nondeveloper observed session remains external.

Evidence: `8b390e6`; `apps/operator_console/index.html`; `tests/browser/`.

## Phase 3 — ingestion hardening

Implemented chunked staging and hashing, atomic content-addressed preservation, encoding detection/override, CSV/JSON/JSONL/structured-text parsing, dotted nested fields, streamed top-level JSON arrays, safe ZIP extraction, versioned mapping profiles, connector contracts, durable retry jobs, and row-error CSV download. A 50 MB generated stream is checked against bounded staging allocation. A named real-export profile remains data-gated.

Evidence: `48fefd0`, `23d7bab`; `tests/unit/test_ingestion_hardening.py`; `tests/contract/`.

## Phase 4 — incident intelligence

Implemented lifecycle markers, provenance-bearing duration metrics, separate technical/business recovery, uncertainty intervals and order flags, clock-alignment evidence, event grouping, incident suggestions, dependency impact, recurrence matching, and comparison endpoints/UI.

Evidence: `a34968a`; incident/timeline unit and integration suites.

## Phase 5 — evidence methodology

Implemented a versioned confidence policy, evidence strength and origin-group caps, alternatives, contradiction approval blocks, expected-source templates, reviewer agreement records, and explainable data-quality dimensions. Real-case calibration/inter-rater measurement remains external.

Evidence: `c01f4ca`; `config/confidence_policy_v1.yaml`; `docs/methodology/confidence_method.md`.

## Phase 6 — buyer reports

Implemented executive, technical, and vendor profiles from one structured snapshot; template/generator/hash metadata; evidence references; quality blockers; redaction audit; version comparison; and dependency-free PDF generation. Target-buyer interviews remain external.

Evidence: `db4be61`; `tests/unit/test_buyer_reports.py`; `docs/sample_diagnostic/`.

## Phase 7 — security and operations

Implemented server-side tenant scoping and cross-tenant tests, OIDC-ready identity boundary, role checks, rate limiting, failure audit, optional streamed AES-GCM raw-evidence encryption, TLS Compose overlay, JSON logs, health/metrics/alerts, independent retention approval and receipts, encrypted-backup option, and CI security/SBOM jobs. Independent/customer security acceptance remains external.

Evidence: `24ec06d`; `tests/security/`; `docs/security/`; `deployment/on_prem/secure_install.md`.

## Phase 8 — release quality

Added property/fuzz, concurrency, fault, migration replay, backup/restore, release-gate, load, PostgreSQL CI, browser CI, and clean-machine automation. Migration replay found and corrected historical SQLite/Alembic incompatibilities. A timed independent target-host install/restore remains deployment-gated.

Evidence: `701ea83`; `.github/workflows/`; `tests/property/`, `tests/fault/`, `tests/migrations/`, `tests/load/`.

## Phase 9 — real-data enablement

Added an ignored private-data boundary, secret/private-data scanning, deterministic anonymisation, dataset fingerprints, permission metadata, and import-effort records. No customer dataset is represented in Git; the first real diagnostic remains external.

Evidence: `01f8a4f`; `scripts/scan_private_data.py`; `scripts/anonymize_dataset.py`; `docs/customer_data_pack/`.

## Phase 10 — commercial enablement

Added versioned diagnostic/pilot offer structures, a proposal generator with scope/data/security/change-control language, and a conservative reuse calculator that counts manual and customer-specific work in the denominator. No proposal acceptance, payment, pricing validation, introduction, or partner commitment is claimed.

Evidence: `6fe6548`; `config/commercial_offers.yaml`; `scripts/generate_proposal.py`; `scripts/calculate_reuse.py`.

## Verification and remaining gates

The final verification commands and exact results are recorded in `docs/CURRENT_STATUS_FOR_PLAN_COMPARISON.md`. Remaining gates all require external evidence: a permitted real export and diagnostic, operator outcome review, two buyer reviews/pricing signals, a nondeveloper usability observation, independent/customer security review, clean target deployment acceptance, paid work, second-deployment reuse, and partner commitments.
