# Evidence ledger

| Evidence | Type | Scope | Synthetic | Supports |
|---|---|---|---:|---|
| `docs/phase_reports/phase_00_conversion_baseline.md` | verification report | Git and ROS baseline | no | preserved autonomy regression |
| `docs/phase_reports/phase_02_historical_ingestion.md` | phase report | generic historical ingestion | yes | ingestion/provenance |
| `tests/end_to_end/test_diagnostic_workflow.py` | automated test | three-source diagnostic to approved ZIP | yes | timeline, incident, evidence, reports |
| `docs/phase_reports/phase_07_pilot_readiness.md` | deployment report | Compose, PostgreSQL, backup/restore | no customer data | security/deployment |
| `fixtures/incident_001_door_wifi/manifest.yaml` | fixture manifest | door/Wi-Fi ambiguity | yes | demonstration only |
| `docs/validation/confidence_board.md` | validation policy | no real validation recorded | no | commercial score remains 1/5 |

Real customer evidence must be stored outside public Git when sensitive. The ledger may reference a fingerprint or access-controlled record without exposing contents.
# Maximum-score implementation evidence — 2026-07-19

| Area | Evidence | What it supports | External gate |
|---|---|---|---|
| Console | `8b390e6`, `tests/browser/` | Browser diagnostic and role journeys | Observed nondeveloper session |
| Ingestion | `48fefd0`, `23d7bab`, `tests/unit/test_ingestion_hardening.py` | Streaming, formats, ZIP, profiles, jobs | Permitted real export profile |
| Incident intelligence | `a34968a`, `tests/unit/test_incident_timing.py` | Lifecycle, metrics, uncertainty, clock evidence | Real-case usefulness |
| Evidence method | `c01f4ca`, `config/confidence_policy_v1.yaml` | Versioned explainable policy | Calibration and inter-rater record |
| Reports | `db4be61`, `docs/sample_diagnostic/` | Profiles, quality, redaction, PDF | Two target-user reviews |
| Security | `24ec06d`, `tests/security/`, `docs/security/customer_security_pack/` | Isolation, encryption, operations baseline | Independent/customer review |
| Release | `701ea83`, CI workflows, release tests | Migration, fault, load, SBOM/release automation | Clean target-host acceptance |
| Data intake | `01f8a4f`, `docs/customer_data_pack/` | Private-data controls and effort records | First permitted dataset |
| Commercial tools | `6fe6548`, `config/commercial_offers.yaml` | Proposals and reuse calculation | Payment/pricing/partner evidence |

The technical score is 91/100. No synthetic fixture, template, or automated test awards commercial-validation points.
