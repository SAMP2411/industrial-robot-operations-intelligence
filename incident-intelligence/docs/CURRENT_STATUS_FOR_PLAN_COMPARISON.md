# Current project status for plan comparison

**Status date:** 2026-07-19

**Project:** Robot Fleet Incident Intelligence

**Branch:** `max-score/10-commercial-enablement`

**Defensible score:** 91/100

**Commercial status:** technically mature and validation-ready; no real-customer or payment validation is claimed

## Paste-ready summary

This repository is a read-only historical incident-diagnostic platform for robot fleets and connected warehouse/factory systems. It accepts imperfect exports from robots, fleet managers, WMS/WCS/WES, PLC/automation, doors/lifts/conveyors/chargers, Wi-Fi/network systems, maintenance systems, and neutral ROS-derived data. It preserves original evidence, normalizes canonical events with provenance, maps assets, reconstructs uncertainty-aware cross-system timelines, measures downtime and technical/business recovery, compares evidence-linked hypotheses, discloses contradictions/missing sources/data quality, and generates human-approved executive, technical, PDF, and vendor-support outputs. It does not control robots or production systems, autonomously confirm root cause, or claim predictive maintenance.

The repository-controlled technical roadmap is implemented through phase 10. The score rose from 82 to 91 because the browser workflow, incident/timeline model, security baseline, ingestion hardening, and release evidence are now present. Nine points are deliberately withheld until real export, usability, buyer-review, security-review, and commercial evidence exists.

The repository structure was streamlined after this implementation: active product code remains in `apps/`, `packages/`, and `connectors/`, while the previous ROS/Gazebo/FleetWatch project and its historical documentation are isolated under `legacy/autonomy_demo/`. The complete current repository map and 37-step runtime flow are documented in `docs/SYSTEM_FEATURE_AND_CODE_FLOW.md`.

## Current capabilities

### Analyst workflow

A single browser console provides engagement setup; source registration; upload preview, preservation, and explicit commit; encoding/profile controls; asset/system mapping review; incident and interactive timeline workspaces; clock-offset editing; downtime/recovery editing; hypotheses/evidence and quality review; executive/technical/vendor report generation; redaction; approval; vendor-package selection; role-aware administration; and validation records. Nine named Playwright journeys cover the core workflow and roles. Normal analyst work does not require OpenAPI.

### Intake and evidence preservation

Uploads are staged in chunks with incremental SHA-256, size limits, atomic content-addressed storage, and optional streamed AES-GCM at-rest encryption. Preview and normalization stream CSV, JSONL, structured text, and top-level JSON arrays instead of rereading the full file. The parser supports encoding detection/override, duplicate/empty CSV headers, delimiter variation, dotted nested field paths, regex structured-text profiles, row-level errors and CSV download, safe ZIP bundles, profile versioning, immutable raw provenance, idempotency, concurrent intake, and durable retry jobs. Generic connector contracts are tested; no named real vendor export is certified yet.

### Incident intelligence

The domain records lifecycle markers from detection through technical and business recovery. Operational duration metrics include derivation/provenance or an explicit unavailable reason. Timeline ordering represents uncertainty intervals, clock alignment cites evidence, and event groups, incident suggestions, dependency impact, recurrence matching, and incident comparison are available. Raw events remain traceable to source filename, row, timestamp, and record hash.

### Evidence and reports

A versioned confidence policy models support, contradiction, context, missing expected evidence, strength, and origin-group independence. Duplicated evidence origins are capped. Medium/high-severity approval requires an alternative hypothesis or explicit reviewer justification; unresolved contradictions block approval. Reviewer agreement/disagreement and explainable quality dimensions are recorded.

Executive, technical, and vendor profiles derive from one structured report snapshot. Quality checks block unsupported certainty or incomplete approval. Outputs include JSON, Markdown, HTML, dependency-free PDF, timeline CSV, evidence manifest, and deterministic selected-evidence ZIP. Redaction is previewed/audited, versions are comparable, and approved artifacts are immutable. The committed sample is conspicuously labelled `SYNTHETIC DEMONSTRATION — NOT CUSTOMER DATA`.

### Security and operations

The application has server-side tenant scoping with cross-tenant tests, role permissions, an OIDC-ready identity boundary, development-only local-header mode, login throttling, failure audit, JSON request logs, health checks, Prometheus metrics and alerts, TLS Compose overlay, retention preview plus independent deletion approval/receipt, backup/restore tooling with optional `age` encryption, migration replay tests, CI dependency/static/secret/container scans, and tagged-release SBOM/manifest generation. A STRIDE threat model, secure-install guide, customer security pack, incident/vulnerability/update/retention policies, and external-review form exist.

### Real-data and commercial enablement

Private datasets are excluded from Git and scanned before release. Dataset registrations store fingerprint/permission metadata without contents. A deterministic anonymizer, customer intake pack, import-effort records, proposal generator, versioned offer structures, and conservative reuse calculator exist. These are enablement tools, not market evidence.

## Verification recorded on 2026-07-19

| Verification | Result |
|---|---|
| Test collection | 99 tests |
| Browser suite | 9 passed |
| Remaining suite | 87 passed, 2 skipped; no failures |
| Scorecard validator | `Scorecard valid: 91/100` |
| Product-claim lint | passed |
| Private-data scan | passed |
| Release gate without duplicate test run | passed |
| Alembic head | `0008_dataset_enablement (head)` |
| Standard Compose config | passed with non-secret check values |
| TLS Compose overlay config | passed with non-secret check values |
| Synthetic sample checks | PDF signature, label, ZIP label passed |

The browser server’s cold start exceeded an old fixed polling window during verification. The fixture now uses a 90-second monotonic deadline; all nine browser tests pass afterward. The two skipped tests are environment-dependent and are not represented as completed external acceptance.

## Git implementation history

| Commit | Phase |
|---|---|
| `b4a55a8`, `c3d2802` | Scorecard, evidence ledger, scope/claim guardrails |
| `8b390e6` | Complete analyst browser console and E2E |
| `48fefd0`, `23d7bab` | Ingestion, connector, streaming, parsing, jobs, row errors |
| `a34968a` | Lifecycle, metrics, uncertainty, clock/event/recurrence intelligence |
| `c01f4ca` | Versioned evidence and confidence methodology |
| `db4be61` | Buyer report profiles, redaction, comparison, PDF |
| `24ec06d` | Tenant security and pilot operations |
| `701ea83` | Reliability, migration, load/fault, CI and release gates |
| `01f8a4f` | Private real-data enablement and import effort |
| `6fe6548` | Commercial proposal and reuse tools |

The final documentation/status commit follows these implementation commits, satisfying the requirement to update documentation only after code changes.

## Roadmap comparison

| Roadmap area | Current state | What prevents maximum evidence score |
|---|---|---|
| Phase 1 guardrails | Implemented and checked | None |
| Phase 2 analyst console | Implemented and browser-tested | One observed nondeveloper session |
| Phase 3 ingestion | Generic technical acceptance implemented | First permitted real export profile |
| Phase 4 incident/timeline | Technical acceptance implemented | Real-case usefulness still unmeasured |
| Phase 5 evidence methodology | Technical acceptance implemented | Real calibration and inter-rater evidence |
| Phase 6 buyer reports | Technical acceptance and synthetic sample implemented | Two target-user reviews |
| Phase 7 security/operations | Repository baseline implemented | Independent/customer review and target-environment acceptance |
| Phase 8 release quality | Automated gates implemented | Timed clean target-host install/restore/load record |
| Phase 9 real-data intake | Safeguards/workflows implemented | First permitted real dataset and operator-reviewed outcome |
| Phases 10–14 commercial validation | Templates and measurement tools implemented | Payment, second diagnostic, ≥70% reuse, partner introductions/commitment, pricing interviews, named-account census |

## External evidence still required

The unchecked items in `next.md` are intentional and cannot be truthfully completed from repository work alone:

1. Obtain permission and register the first real operator export; build and test its named mapping profile.
2. Run a real diagnostic with pre-analysis notes, import-effort measurement, operator review, and an actionable-outcome record.
3. Observe a nondeveloper completing the browser workflow without developer assistance.
4. Conduct two target-buyer report/pricing reviews and record willingness-to-pay behavior.
5. Perform a clean target-machine install, encrypted backup/restore/load drill, and independent or customer security review.
6. Complete paid work, a second diagnostic, and the conservative reuse calculation; only award reuse if it reaches 70% or explain failure.
7. Obtain two partner introductions, one written commercial commitment, annual-pricing evidence, and the named-account census.

Sensitive customer evidence belongs outside public Git. Store only approved anonymised claims or access-controlled fingerprints/references in the evidence ledger.

## Recommended ChatGPT comparison prompt

> Compare my plan against this status document and `next.md`. Treat checked roadmap items as repository-verified technical implementation, not customer validation. Treat every unchecked external-evidence item as a real blocker. Identify the shortest sequence that tests data access, operator usefulness, buyer willingness to pay, security acceptance, and second-deployment reuse. Do not recommend additional speculative features unless one of those tests exposes a concrete gap.
