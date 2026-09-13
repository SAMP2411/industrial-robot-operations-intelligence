# System features and code flow

This document explains where everything lives, how a request moves through the code from browser to final report, why each capability exists, and which alternatives were considered. The active product is entirely separate from `legacy/autonomy_demo/`.

## Repository map

```text
onpoint-monitoring-startup/
├── apps/                 # User-facing API, browser console, and worker entry points
├── packages/             # Reusable product domain and service modules
├── connectors/           # Read-only evidence adapter implementations
├── config/               # Versioned business/methodology policies
├── fixtures/             # Clearly labelled synthetic diagnostic datasets
├── data/private/         # Git-ignored customer-data boundary
├── deployment/           # Database migrations, container, TLS, monitoring, backup
├── scripts/              # Release, validation, anonymisation, proposal, and load tools
├── tests/                # Tests grouped by behavior and risk
├── docs/                 # Current product, operation, validation, and status documentation
├── legacy/autonomy_demo/ # Isolated older ROS/Gazebo/FleetWatch demonstration
├── tools/                # Active-product administrator utility
├── next.md               # Evidence-aware implementation/validation roadmap
└── README.md             # First entry point
```

Why this shape: active product code stays at predictable Python import paths, while the older robotics application and its historical documentation are kept together behind a visible `legacy/` boundary. Moving active packages into another wrapper such as `src/product/` was rejected because it would add import churn without improving domain ownership. Deleting the old demonstration was rejected because it remains useful for regression and synthetic evidence generation.

## Main runtime flow

| Step | Feature and one-line behavior | Code path | Why it exists | Alternative considered and why not chosen |
|---:|---|---|---|---|
| 1 | Configuration loads database, storage, authentication, encryption, retention, and request limits. | `packages/common/config.py` | Keeps environment differences outside business logic. | Hard-coded settings were rejected because pilot deployments need different secrets, storage, and identity controls. |
| 2 | FastAPI creates the application, schema boundary, dependencies, middleware, health routes, and API routes. | `apps/diagnostic_api/main.py` | Provides one explicit HTTP entry point for the product. | Multiple deployable microservices were rejected because current scale does not justify operational complexity. |
| 3 | JSON request logging, request IDs, timing, rate limits, and metrics wrap every API request. | `packages/common/observability.py`, `packages/common/security.py` | Makes failures and abuse observable without changing domain services. | Endpoint-specific logging was rejected because it produces inconsistent coverage. |
| 4 | Authentication resolves a local development identity or an OIDC-ready principal, then role permissions authorize the action. | `packages/common/auth_provider.py`, `packages/common/security.py` | Separates identity proof from product permissions. | Custom production passwords alone were rejected because customer identity providers and MFA should remain authoritative. |
| 5 | Tenant scoping resolves the customer behind each entity before data is read or changed. | `apps/diagnostic_api/main.py`, `tests/security/test_tenant_scope.py` | Prevents cross-customer data exposure at the server boundary. | UI-only filtering was rejected because API calls can bypass a browser. |
| 6 | The browser console loads the incident-first workspace and calls JSON/multipart APIs. | `apps/operator_console/index.html` | Lets a nondeveloper analyst complete normal work without OpenAPI. | A separate JavaScript build toolchain was deferred because the current single-page console is small and dependency-light. |
| 7 | Engagement setup creates customer, site, system, asset, dependency, engagement, and expected-source records. | `apps/diagnostic_api/schemas.py`, `packages/domain_models/models.py` | Establishes ownership and expected evidence before analysis begins. | Free-form case folders were rejected because they cannot enforce provenance, tenancy, or consistent reports. |
| 8 | Asset-registry import converts the preserved YAML registry into product systems/assets. | `apps/diagnostic_api/main.py`, `packages/asset_mapping/matcher.py` | Reuses permitted brownfield asset definitions without connecting to live control systems. | Direct live registry synchronization was rejected for the read-only first product. |
| 9 | Upload staging reads chunks, enforces size, computes SHA-256, and cleans partial files. | `apps/diagnostic_api/main.py` (`stage_upload`) | Keeps memory bounded and identifies exact evidence bytes. | Reading the multipart body into memory was rejected because large customer exports can exhaust the API process. |
| 10 | Preview detects format/encoding, streams rows, samples records, checks timestamps, and proposes asset mappings without persisting evidence. | `packages/ingestion_core/service.py` (`preview_path`) | Gives the analyst a safe correction point before preservation. | Immediate automatic import was rejected because imperfect field and asset mappings require human review. |
| 11 | CSV, JSON arrays, JSONL, and regex structured text normalize into record dictionaries with nested-field support and downloadable row errors. | `packages/ingestion_core/service.py` | Covers common export shapes with explicit failure evidence. | A broad ETL dependency was rejected because the supported formats need a smaller auditable surface. |
| 12 | ZIP intake rejects traversal, links, encryption, nesting, excessive ratios, and unsafe contents before extraction. | `packages/ingestion_core/archive.py` | Accepts evidence bundles without exposing the host to common archive attacks. | Blind OS extraction was rejected because archive paths and expansion are attacker-controlled. |
| 13 | Explicit preserve writes the original file atomically under its content hash and optionally encrypts it with AES-GCM. | `packages/ingestion_core/service.py`, `packages/common/encryption.py` | Makes later findings traceable to immutable source evidence. | Keeping only normalized rows was rejected because analysts and vendors must be able to inspect the original record. |
| 14 | Explicit commit creates immutable raw records and canonical events with timestamp, asset, source, and row provenance. | `packages/ingestion_core/service.py`, `packages/event_normalization/timestamps.py` | Separates evidence preservation from interpretation. | Overwriting raw rows during cleanup was rejected because it destroys auditability. |
| 15 | Mapping review resolves exact/alias matches and exposes unknown or ambiguous assets. | `packages/asset_mapping/matcher.py` | Avoids silently attaching events to the wrong machine. | Fuzzy auto-acceptance was rejected because a plausible wrong mapping is more dangerous than an explicit unknown. |
| 16 | Durable jobs claim, heartbeat, retry, fail, and complete idempotent background work. | `packages/job_queue/service.py`, `apps/report_worker/worker.py` | Allows recoverable long-running intake/report tasks. | In-memory task queues were rejected because process restarts would lose state and audit history. |
| 17 | Incident boundaries and lifecycle markers distinguish detection, response, mitigation, technical recovery, business recovery, and closure. | `packages/incident_engine/service.py` | Makes operational durations reproducible instead of relying on one vague “resolved” time. | A single duration field was rejected because technical availability and business recovery often differ. |
| 18 | Timeline construction merges sources, applies clock evidence, preserves uncertainty intervals, groups events, and cites raw evidence. | `packages/timeline_engine/service.py` | Produces a defensible chronology while showing what ordering is uncertain. | Silently forcing every event into a precise order was rejected because source clocks are imperfect. |
| 19 | Incident analysis suggests candidate windows, explains dependency impact, compares incidents, and finds recurrence matches. | `packages/incident_analysis/service.py` | Speeds analyst review without turning suggestions into autonomous conclusions. | Automatic incident/root-cause confirmation was rejected because evidence quality and operational context require a human. |
| 20 | Downtime/recovery metrics return a value plus derivation/provenance, or an explicit unavailable reason. | `packages/incident_engine/service.py` | Prevents unsupported operational numbers from appearing definitive. | Defaulting missing durations to zero was rejected because zero is a real measurement, not missing data. |
| 21 | Hypotheses link supporting, contradicting, contextual, and missing-expected evidence with strength and origin independence. | `packages/hypothesis_engine/service.py`, `config/confidence_policy_v1.yaml` | Makes reasoning inspectable and prevents copied evidence from looking independent. | Opaque ML/LLM confidence was rejected because customers need a stable explainable method. |
| 22 | Reviewer decisions, alternative-hypothesis rules, and unresolved contradictions gate confirmation and report approval. | `packages/report_generation/service.py`, domain review models | Preserves human accountability for causal claims. | First-hypothesis-wins approval was rejected because it encourages confirmation bias. |
| 23 | Data-quality assessment scores source completeness, time, identity, normalization, critical coverage, integrity, independence, and contradiction state. | `packages/data_quality/service.py`, `config/expected_source_templates.yaml` | Shows whether the evidence can support the desired conclusion. | One unexplained quality percentage was rejected because users need to know what is missing. |
| 24 | Corrective actions and recovery actions record what was proposed, performed, by whom, when, and with what outcome. | `packages/domain_models/models.py`, incident API routes | Connects evidence to an operational follow-up without controlling equipment. | Direct work-order or PLC writes were rejected to preserve the product’s read-only safety boundary. |
| 25 | Report generation builds executive, technical, and vendor views from one versioned structured snapshot. | `packages/report_generation/service.py`, `config/report_profiles.yaml` | Keeps audiences consistent while varying detail. | Separately authored reports were rejected because facts and versions would drift. |
| 26 | Redaction masks configured identifiers and records preview/application counts in an audit record. | `packages/report_generation/redaction.py` | Reduces disclosure before a report or vendor package leaves the analyst boundary. | Irreversible deletion during ingestion was rejected because internal diagnosis may still need original evidence. |
| 27 | PDF generation renders the same structured report without a browser/runtime dependency. | `packages/report_generation/pdf.py` | Provides a portable buyer artifact with deterministic generation. | Headless-browser PDF rendering was rejected for now because it adds a large runtime and nondeterministic layout surface. |
| 28 | Vendor packaging includes only explicitly selected raw evidence plus hashes, questions, timeline, and limitations. | `packages/report_generation/service.py` | Applies data minimization to third-party support sharing. | Packaging every uploaded file was rejected because it exposes unrelated or sensitive evidence. |
| 29 | Approval marks a report version immutable; regeneration creates a new version and comparison exposes changes. | `packages/report_generation/service.py`, report artifact model | Protects the exact reviewed deliverable. | Editing an approved file in place was rejected because its hash and approval would become misleading. |
| 30 | Audit events record actor/action/entity/details and reject application-layer mutation. | `packages/audit/service.py`, `packages/domain_models/models.py` | Supports accountability across uploads, analysis, reports, and deletion. | Ordinary mutable application logs were rejected because they are not a durable domain audit trail. |
| 31 | Retention preview calculates scope, a second actor approves it, execution removes scoped data, and a receipt remains. | `packages/retention/service.py` | Makes destructive lifecycle actions deliberate and reviewable. | One-click recursive deletion was rejected because target mistakes are difficult to recover from. |
| 32 | Dataset registration stores permission, fingerprint, and effort metadata while customer contents stay outside Git. | dataset API/models, `data/private/`, `scripts/scan_private_data.py` | Enables honest real-data validation without publishing sensitive evidence. | Committing anonymized-looking exports was rejected because residual identification risk remains. |
| 33 | Anonymisation deterministically replaces identifiers and emits a transformation manifest. | `scripts/anonymize_dataset.py` | Preserves cross-source joins while reducing identity exposure. | Random replacement was rejected because repeated identifiers would no longer correlate. |
| 34 | Proposal and reuse tools turn engagement scope into consistent offers and measure reusable versus customer-specific effort. | `scripts/generate_proposal.py`, `scripts/calculate_reuse.py`, `config/commercial_offers.yaml` | Connects technical delivery to honest commercial validation. | Subjective “mostly reusable” claims were rejected because manual work must remain in the denominator. |
| 35 | Health, Prometheus metrics, alert rules, backup/restore, TLS proxy, and container definitions operate the pilot deployment. | `deployment/`, `packages/common/observability.py` | Supplies a reviewable on-premises operational baseline. | Kubernetes and multi-region SaaS were rejected as premature for the present pilot scope. |
| 36 | Alembic applies versioned schema changes and replay tests exercise upgrade/downgrade/upgrade behavior. | `deployment/migrations/`, `tests/migration/` | Makes database evolution reproducible. | `create_all` as the production upgrade mechanism was rejected because it cannot review or reverse changes. |
| 37 | The release gate combines tests, scorecard, claim lint, private-data scan, migration head, scans, SBOM, and manifest workflows. | `scripts/release_gate.py`, `.github/workflows/` | Prevents incomplete evidence from being treated as a release. | A manual checklist alone was rejected because repeated checks are easily skipped. |

## Data objects from start to finish

```text
Customer → Site → System/Asset/Dependency
                    ↓
DiagnosticEngagement → DataSource → IngestionRun
                                      ↓
                               immutable RawRecord
                                      ↓
                               CanonicalEvent
                                      ↓
Incident → Timeline/Lifecycle/Downtime/Recovery/DataQuality
                                      ↓
                    Hypothesis ↔ Evidence ↔ Reviewer decision
                                      ↓
                 Structured report snapshot → approved artifacts
                                      ↓
                 Executive PDF / technical files / minimal vendor ZIP
```

## Test flow

The fastest confidence path is: unit/property parser and domain tests → connector contracts → API integration and tenant-security tests → migration/fault/load/backup tests → nine browser journeys → complete end-to-end diagnostic → release gate. Tests are grouped by risk under `tests/` so a contributor can run the narrowest relevant group before the full suite.

## Boundaries that must remain true

- The active product never imports `legacy/autonomy_demo/`, ROS, Gazebo, or Nav2.
- Connectors and the API read exported evidence; they do not control production equipment.
- Raw evidence, audit events, and approved reports remain immutable through normal application paths.
- Synthetic fixtures demonstrate behavior but never count as customer or commercial validation.
- Root-cause confirmation, vendor sharing, report approval, and destructive retention actions require accountable humans.
