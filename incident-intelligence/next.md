# NEXT.md — Maximum-Score Roadmap for Robot Fleet Incident Intelligence

**Repository:** `onpoint-monitoring-startup`

**Working branch:** `startup-incident-intelligence`

**Roadmap purpose:** Move the current project from an evidence-based score of approximately **82/100** to the maximum defensible score across product, engineering, pilot readiness, analyst usability, security, and commercial validation.

---

# 0. Executive instruction

The current repository is no longer an early prototype. It is already a validation-ready technical MVP with:

- read-only historical evidence ingestion;
- canonical events with provenance;
- asset and system mapping;
- cross-system incident timelines;
- clock-offset handling;
- downtime and recovery modelling;
- evidence-linked hypotheses;
- explicit data-quality limitations;
- diagnostic reports;
- vendor-support packages;
- role-based access;
- audit records;
- PostgreSQL migrations;
- Docker Compose;
- backup and restore;
- three synthetic incident fixtures;
- a preserved ROS 2 autonomy demonstration.

The next stage must **not** repeat already-completed conversion work.

The roadmap must close the remaining score gaps:

1. make the entire analyst workflow usable through the browser without relying on OpenAPI;
2. harden ingestion for imperfect and large real-world exports;
3. complete operational timing, incident, recovery, and recurring-pattern metrics;
4. strengthen evidence review, confidence calibration, and data-quality methods;
5. produce buyer-ready reports and support packages;
6. add production-grade CI, browser tests, monitoring, secure deployment, tenant scoping, and security evidence;
7. process real operator data;
8. obtain operator-reviewed outcomes;
9. test willingness to pay;
10. secure at least one pilot or partner commitment.

The final ten to twenty points cannot be earned by code alone.

Codex can build the product, tooling, workflows, templates, metrics, and evidence collection system. The founder must obtain customer data, conduct interviews, present reports, ask for payment, and secure written commitments.

---

# 1. Current baseline and target score

## 1.1 Current evidence-based score

| Category | Weight | Current | Target |
|---|---:|---:|---:|
| Product direction and scope | 10 | 10 | 10 |
| Architecture and domain model | 10 | 10 | 10 |
| Historical ingestion and provenance | 10 | 9 | 10 |
| Timeline and timestamp handling | 15 | 13 | 15 |
| Incident, downtime, and recovery | 10 | 8 | 10 |
| Hypotheses, evidence, and data quality | 10 | 9 | 10 |
| Reports and vendor-support package | 10 | 9 | 10 |
| Security, deployment, and testing | 10 | 8 | 10 |
| Analyst console and usability | 10 | 5 | 10 |
| Real-world and commercial validation | 5 | 1 | 5 |
| **Total** | **100** | **82** | **100** |

## 1.2 Meaning of a maximum score

A maximum score is not a claim that the product is perfect or finished forever.

It means that the startup has defensible evidence for the current stage:

- the technical workflow works end to end;
- a nondeveloper analyst can operate it;
- real industrial exports have been processed;
- the output has been reviewed by real users;
- important security and deployment controls have been tested;
- the diagnostic has changed or supported a real decision;
- at least one buyer has paid or made a concrete pilot commitment;
- reuse is measured across more than one diagnostic;
- remaining limitations are documented rather than hidden.

## 1.3 Hard rule

Never mark the commercial category complete using:

- synthetic fixtures;
- conversations only with friends who are not target users;
- fake customer records;
- fake quotes;
- hypothetical pricing;
- generated testimonials;
- self-reviewed reports;
- a demo that uses only internally generated data.

---

# 2. Two-track execution model

All work must run in two parallel tracks.

## Track A — Codex implementation

Codex is responsible for:

- browser workflow;
- ingestion hardening;
- analysis completeness;
- reporting quality;
- security controls;
- deployment tooling;
- automated tests;
- validation-record tooling;
- customer-data import utilities;
- reusable mapping profiles;
- documentation;
- phase reports;
- evidence capture.

## Track B — Founder validation

The founder is responsible for:

- recruiting operators and integrators;
- requesting real incident data;
- agreeing data-handling terms;
- conducting interviews;
- reviewing diagnostic outputs with users;
- recording whether a decision changed;
- asking for money;
- sending proposals;
- collecting written pilot or partner commitments;
- recording objections;
- making go, pivot, or stop decisions.

## Synchronisation rule

Codex must not build speculative features merely because Track B is slow.

When founder evidence is unavailable, Codex should work only on:

- already identified usability blockers;
- security and reliability controls required for a real pilot;
- test coverage;
- sample diagnostic polish;
- reusable import tooling;
- documentation needed to obtain data.

Do not build broad live connectors, predictive maintenance, fleet control, or an AI chatbot while waiting for a customer.

---

# 3. Repository working rules for Codex

Codex must follow these rules on every phase.

## 3.1 Baseline first

Before changing code:

```bash
git status
git branch --show-current
git log -5 --oneline
pytest
docker compose config
```

Record results in the phase report.

## 3.2 Branch strategy

Create one branch per major phase:

```text
max-score/01-scorecard-and-guardrails
max-score/02-analyst-console
max-score/03-ingestion-hardening
max-score/04-timeline-and-metrics
max-score/05-evidence-and-quality
max-score/06-reporting
max-score/07-security-and-operations
max-score/08-test-and-release
max-score/09-real-data-enablement
max-score/10-partner-and-commercial
```

If the work is executed directly on the current feature branch, create small commits and preserve the same phase boundaries.

## 3.3 Commit rules

Use intentional commits:

```text
feat(console): add guided engagement creation
feat(ingestion): stream uploads into content-addressed storage
feat(timeline): add uncertainty-aware ordering
feat(metrics): calculate detection and acknowledgment durations
feat(report): add executive and technical report profiles
feat(security): enforce tenant scope in repository layer
test(e2e): cover analyst diagnostic workflow
docs(validation): add real-dataset review protocol
```

Do not create one giant commit containing the entire roadmap.

## 3.4 Phase report

After each phase, create:

```text
docs/phase_reports/max_score_phase_XX.md
```

Every phase report must contain:

- purpose;
- baseline commit;
- final commit;
- files changed;
- migrations added;
- commands executed;
- test results;
- screenshots or generated artifacts;
- acceptance criteria;
- remaining limitations;
- whether any score can be increased;
- evidence location.

## 3.5 No silent scope changes

If a planned task is impossible or inappropriate after repository inspection:

1. document the reason;
2. implement the smallest correct alternative;
3. update this file;
4. do not silently omit the task.

## 3.6 Preserve product boundaries

No new feature may:

- control a robot;
- change customer production state;
- send PLC write commands;
- replace a WMS/WCS;
- autonomously confirm a root cause;
- hide conflicting evidence;
- claim automatic clock alignment without verification;
- claim predictive maintenance.

---

# 4. Phase 1 — Scorecard, evidence ledger, and regression guardrails

## Goal

Create a machine-readable system that prevents the project from claiming points without evidence.

## Score impact

This phase protects all categories and stops future documentation drift.

## 4.1 Create scorecard files

Create:

```text
docs/scorecard/current_score.yaml
docs/scorecard/scoring_rubric.md
docs/scorecard/evidence_ledger.md
scripts/validate_scorecard.py
tests/contract/test_scorecard_evidence.py
```

## 4.2 Scorecard schema

Example:

```yaml
scorecard_version: "1.0"
status_date: "YYYY-MM-DD"
categories:
  analyst_console:
    weight: 10
    score: 5
    target: 10
    evidence:
      - docs/phase_reports/max_score_phase_02.md
    blockers:
      - "Upload and mapping workflow still depends on OpenAPI"
    completion_conditions:
      - "Full E2E diagnostic completed through browser"
      - "Playwright workflow passes"
  commercial_validation:
    weight: 5
    score: 1
    target: 5
    evidence:
      - validation/confidence_board/current.md
    blockers:
      - "No real dataset"
      - "No paid diagnostic"
```

## 4.3 Evidence requirements

Every score increase must link to one or more of:

- test result;
- screenshot;
- generated report;
- deployment verification;
- real customer review notes;
- anonymised dataset identifier;
- signed or written pilot commitment;
- invoice/payment evidence reference;
- security review result;
- phase report.

## 4.4 Add scope regression tests

Create tests that verify:

- no startup-facing API contains robot-control endpoints;
- no product UI exposes mission dispatch;
- product README identifies the system as read-only;
- `legacy/autonomy_demo` is not imported by the incident API;
- report wording does not claim confirmed causality without approved human review;
- synthetic fixtures are visibly labelled synthetic.

## 4.5 Add claim linting

Create:

```text
scripts/lint_product_claims.py
config/disallowed_unverified_claims.yaml
```

Flag terms such as:

```text
production-ready
validated pricing
proven MTTR reduction
automatic root cause
supports all vendors
predictive maintenance
commercially validated
secure by certification
```

Allow them only when:

- included as explicit non-claims;
- included in historical documentation;
- accompanied by a configured evidence reference.

## 4.6 Acceptance criteria

- [x] scorecard can be validated in CI;
- [x] total score is calculated automatically;
- [x] every awarded point links to evidence;
- [x] product-scope tests pass;
- [x] unverified claims fail the documentation check;
- [x] current score remains approximately 82 until later evidence is added.

---

# 5. Phase 2 — Complete the analyst console

## Goal

A trained analyst must be able to perform the complete diagnostic workflow through the browser without using OpenAPI, direct SQL, shell commands, or developer assistance.

## Score impact

Primary:

- Analyst console and usability: 5 → 10

Secondary:

- Reports: 9 → 10
- Pilot readiness
- Commercial validation readiness

## 5.1 First inspect the current console

Codex must determine:

- current frontend technology;
- current routes and templates;
- authentication flow;
- available components;
- how API calls are made;
- where role checks occur;
- how errors and loading states are handled.

Do not replace the frontend framework unless the current implementation fundamentally blocks the workflow.

Prefer extending the current console.

## 5.2 Required complete workflow

The browser must support:

```text
Login
→ Create customer/site or select existing
→ Create diagnostic engagement
→ Register expected sources
→ Upload and preview files
→ Review validation errors
→ Confirm ingestion
→ Review asset and system mappings
→ Create or open incident
→ Set incident boundaries
→ Adjust clock offsets
→ Filter and annotate timeline
→ Add downtime segments
→ Add recovery actions
→ Create hypotheses
→ Link supporting/contradicting/missing evidence
→ Review data quality
→ Add corrective actions
→ Generate report
→ Review report
→ Approve immutable report
→ Select evidence for vendor package
→ Download outputs
```

## 5.3 Engagement creation wizard

Create a guided wizard.

### Step 1 — Customer and site

Fields:

- customer;
- site;
- area;
- analyst;
- engagement title;
- incident date;
- time zone;
- known affected systems;
- short operational-impact description.

### Step 2 — Data-request checklist

Display expected source categories:

- robot;
- fleet manager;
- WMS/WCS/WES;
- PLC/control;
- door/lift/conveyor;
- charger;
- Wi-Fi/network;
- maintenance ticket;
- operator notes;
- vendor-support history.

Allow each source to be marked:

```text
available
requested
unavailable
not applicable
unknown
```

### Step 3 — Privacy and handling

Require confirmation:

- data is authorised for analysis;
- unnecessary worker data should be excluded;
- retention period is selected;
- customer/site scope is correct.

### Step 4 — Review and create

Show the final engagement summary.

## 5.4 Upload and preview workspace

For each file show:

- filename;
- source category;
- size;
- SHA-256 after preservation;
- detected encoding;
- detected delimiter/format;
- record count;
- detected time range;
- sample records;
- timestamp parser result;
- event mapping profile;
- proposed asset mappings;
- unknown event codes;
- skipped rows;
- warnings and errors.

Actions:

```text
change source type
select mapping profile
edit field mapping
change timezone
set clock-offset hint
download row-error file
cancel
preserve
commit ingestion
```

No ingestion should be committed invisibly.

## 5.5 Mapping review screen

Create queues for:

- exact matches;
- alias matches;
- ambiguous matches;
- unknown assets;
- unknown systems;
- unknown event codes.

Allow:

- assign to an existing asset;
- create a new asset;
- add an alias;
- bulk-map repeated identifiers;
- leave unresolved;
- explain why a match was selected.

Persist the mapping decision and audit actor.

## 5.6 Timeline workspace

Required layout:

```text
Left panel:
- sources
- systems
- assets
- event types
- severity
- time quality
- evidence status

Center:
- zoomable chronological timeline
- uncertainty ranges
- incident boundaries
- downtime segments
- recovery actions
- annotations

Right panel:
- selected event details
- original raw record
- parsed event
- provenance
- evidence links
- analyst note
```

Required operations:

- filter;
- search;
- zoom;
- select range;
- create incident boundary;
- add annotation;
- set event relevance;
- add to hypothesis;
- inspect raw source context;
- adjust source clock offset;
- mark duplicate;
- export selected timeline.

## 5.7 Clock-offset editor

Show:

- source;
- current offset;
- original event time;
- adjusted event time;
- reason;
- supporting shared event;
- uncertainty;
- analyst;
- audit history.

Require explicit save and recalculate.

Display uncertainty when ordering cannot be known precisely.

## 5.8 Downtime and recovery editor

Allow multiple segments.

Required fields:

- start;
- end;
- segment type;
- affected assets;
- business impact;
- excluded/planned status;
- evidence links;
- analyst approval.

Recovery actions:

- timestamp;
- action type;
- actor/team;
- affected asset;
- description;
- outcome;
- evidence;
- whether recovery was temporary or durable.

## 5.9 Hypothesis and evidence studio

For each hypothesis display:

- title;
- failure domain;
- current status;
- current confidence;
- confidence derivation;
- assumptions;
- supporting evidence;
- contradicting evidence;
- contextual evidence;
- missing expected evidence;
- alternative hypotheses;
- reviewer decision.

Actions:

- create;
- edit;
- duplicate as alternative;
- attach evidence;
- change relation;
- mark rejected/inconclusive/supported;
- submit for review;
- confirm only with reviewer permission.

## 5.10 Data-quality panel

Display:

- source completeness;
- timestamp confidence;
- mapping confidence;
- normalisation coverage;
- unknown event percentage;
- missing critical sources;
- contradictions;
- evidence sufficiency;
- confidence caps.

Every metric must link to the underlying records or rules.

## 5.11 Report review and approval

Display a report preview with:

- section navigation;
- unresolved warning banner;
- missing-evidence warnings;
- unapproved hypotheses;
- report-template version;
- data snapshot identifier;
- content hash after generation.

Allow:

- regenerate as a new version;
- compare versions;
- add reviewer note;
- approve;
- reject;
- download available formats.

Approved reports cannot be edited.

## 5.12 Vendor package builder

Let the analyst select:

- timeline range;
- systems;
- assets;
- raw files or records;
- screenshots;
- report sections;
- questions for vendor;
- redactions;
- reason for each inclusion.

Show estimated package contents before generation.

## 5.13 Role-aware UI

Required behavior:

- viewer sees read-only pages;
- analyst performs investigation;
- reviewer approves reports and confirmed hypotheses;
- partner sees only assigned customer data;
- admin manages users and retention;
- disabled actions are hidden or clearly denied.

Backend permissions remain authoritative.

## 5.14 Error, progress, and recovery UX

Implement:

- upload progress;
- ingestion progress;
- background-job status;
- retry for failed normalisation;
- clear validation errors;
- no silent failures;
- safe browser refresh;
- draft persistence;
- unsaved-change warning;
- empty states;
- keyboard-accessible controls.

## 5.15 Accessibility baseline

Meet a practical WCAG 2.1 AA-oriented baseline:

- semantic labels;
- keyboard navigation;
- visible focus;
- sufficient contrast;
- error messages tied to fields;
- table headers;
- screen-reader labels;
- no meaning conveyed only by colour.

## 5.16 Browser tests

Use Playwright unless the existing repository has an equivalent tool.

Create tests covering:

```text
tests/browser/test_login.py
tests/browser/test_engagement_wizard.py
tests/browser/test_upload_preview_commit.py
tests/browser/test_mapping_review.py
tests/browser/test_timeline_editing.py
tests/browser/test_hypothesis_evidence.py
tests/browser/test_report_approval.py
tests/browser/test_vendor_package.py
tests/browser/test_role_permissions.py
```

## 5.17 Usability acceptance test

A person unfamiliar with the code should complete the synthetic Door/Wi-Fi diagnostic using only the browser.

Record:

- total time;
- number of blocked steps;
- number of questions asked;
- number of OpenAPI visits;
- number of developer interventions;
- errors encountered.

Pass condition:

```text
0 OpenAPI visits
0 direct database operations
0 shell commands
0 developer intervention
complete report and vendor package generated
```

Target time after training:

```text
≤ 45 minutes for a prepared synthetic fixture
```

Do not treat the time target as customer value evidence.

## 5.18 Acceptance criteria

- [x] complete workflow works in browser;
- [x] all important write actions have dedicated forms;
- [x] no OpenAPI dependency remains for normal analyst work;
- [x] role-aware behavior is tested;
- [x] browser tests pass;
- [ ] one nondeveloper usability session is recorded;
- [ ] analyst-console score can defensibly reach 10/10.

---

# 6. Phase 3 — Industrial ingestion hardening

## Goal

Process imperfect, large, and inconsistent real exports without losing provenance or exhausting memory.

## Score impact

Historical ingestion and provenance: 9 → 10.

## 6.1 Stream file uploads

Current uploads must not require reading the entire file into memory.

Implement:

```text
request stream
→ bounded temporary file
→ incremental SHA-256
→ validation
→ content-addressed final storage
```

Requirements:

- configurable maximum upload size;
- chunked reads;
- safe cancellation;
- temporary-file cleanup;
- hash verification;
- storage write failure handling;
- no partial committed evidence.

## 6.2 Background job system

Use the existing worker boundary.

Prefer a PostgreSQL-backed job queue to avoid adding unnecessary infrastructure unless the repository already uses another durable queue.

Create entities:

```text
Job
JobAttempt
JobEvent
```

Job types:

- file profile;
- preview;
- preserve;
- ingest;
- normalize;
- recalculate timeline;
- generate report;
- build vendor package;
- retention cleanup.

Required behavior:

- queued;
- running;
- succeeded;
- failed;
- cancelled;
- retrying;
- heartbeat;
- retry count;
- idempotency key;
- error summary;
- full error details available to admins.

Use row locking such as `FOR UPDATE SKIP LOCKED` where supported.

## 6.3 Encoding support

Support at minimum:

- UTF-8;
- UTF-8 with BOM;
- Windows-1252;
- ISO-8859-1.

Use deterministic detection and allow analyst override.

Store:

- detected encoding;
- selected encoding;
- detection confidence;
- replacement-character count;
- decoding warnings.

Never silently discard undecodable bytes.

## 6.4 CSV hardening

Support:

- commas;
- semicolons;
- tabs;
- quoted multiline fields;
- embedded delimiters;
- empty headers;
- duplicate headers;
- variable row lengths;
- locale decimal separators;
- BOM;
- huge rows;
- escaped quotes.

Produce row-level errors with:

- line number;
- raw excerpt;
- error code;
- suggested correction.

## 6.5 JSON hardening

Support:

- arrays;
- objects;
- nested `records`;
- JSONL;
- nested field paths;
- optional flattening;
- invalid trailing line reporting;
- null/missing distinctions.

Do not load a massive JSON array completely into memory. Use streaming parsing where appropriate.

## 6.6 Structured-text parser profiles

Add configurable regex/grok-style profiles.

Example:

```yaml
profile_version: "1.0"
name: "timestamp_level_asset_message"
pattern: '^(?P<timestamp>...)\s+(?P<level>...)\s+(?P<asset>...)\s+(?P<message>.*)$'
```

Store unmatched lines as raw records with a normalisation issue rather than discarding them.

## 6.7 Safe ZIP evidence bundles

Support optional ZIP upload for a customer incident bundle.

Controls:

- reject path traversal;
- reject absolute paths;
- reject symlinks;
- reject encrypted archives unless explicitly supported;
- maximum file count;
- maximum uncompressed size;
- maximum compression ratio;
- no nested archives by default;
- MIME/extension validation per extracted file;
- preserve original ZIP hash and extracted-file hashes.

## 6.8 Mapping profile versioning

Every mapping profile must include:

- name;
- version;
- source type;
- author;
- created date;
- field mappings;
- timestamp rules;
- event-code mapping;
- asset mapping;
- test fixture;
- compatibility notes.

Changing a profile creates a new version.

An ingestion run records the exact version used.

## 6.9 Mapping profile editor

Expose the profile editor in the browser.

Support:

- column selection;
- constants;
- nested paths;
- transformations;
- enum mapping;
- severity mapping;
- event-code mapping;
- timezone;
- timestamp format;
- asset identifier;
- preview against sample rows.

Do not execute arbitrary Python from mapping configurations.

Use a constrained transformation language.

## 6.10 Idempotency and duplicate rules

Define duplicates at three levels:

1. identical file hash;
2. identical source record identity;
3. semantically duplicate canonical event.

Behavior must be explicit:

- skip;
- link existing;
- create new version;
- flag for analyst review.

## 6.11 Very large file test

Create a generated test fixture large enough to validate streaming behavior without making CI impractical.

Recommended:

- CI fixture: 50–100 MB;
- scheduled/manual performance fixture: 500 MB or larger.

Measure:

- peak process memory;
- total time;
- records per second;
- error percentage;
- database batch size;
- storage throughput.

Pass targets should be documented based on the test environment rather than claimed universally.

Minimum engineering condition:

```text
Peak memory does not scale linearly with full upload size.
```

## 6.12 Concurrency

Test:

- two analysts uploading simultaneously;
- duplicate file upload;
- same idempotency key;
- report generation during ingestion;
- worker restart;
- database reconnect;
- failed storage write.

## 6.13 Connector SDK certification harness

Create:

```text
packages/connector_sdk/testing.py
scripts/validate_connector.py
tests/connector_contract/
docs/connectors/connector_validation.md
```

Every connector must pass:

- read-only declaration;
- configuration validation;
- preview;
- raw preservation;
- provenance;
- deterministic normalization;
- no writes;
- health response;
- malformed-record behavior;
- version metadata.

## 6.14 First real export profile

Do not invent a named vendor.

When the founder provides the first real export:

1. copy only an anonymised or permitted sample into secure local fixtures;
2. create a connector/mapping profile;
3. add contract tests;
4. document unsupported fields;
5. measure custom engineering time;
6. reuse the generic core;
7. do not place vendor-specific logic in the incident engine.

## 6.15 Acceptance criteria

- [x] streaming upload implemented;
- [x] durable job processing implemented;
- [x] encoding override works;
- [x] CSV/JSON edge cases tested;
- [x] safe ZIP handling tested;
- [x] profile versioning exists;
- [x] large-file memory behavior measured;
- [x] concurrent ingestion tests pass;
- [ ] first real export profile added when data becomes available;
- [ ] ingestion score can reach 10/10 after real-data evidence.

---

# 7. Phase 4 — Complete timeline, incident, and operational metrics

## Goal

Provide a complete, explainable incident chronology with uncertainty and all important operational timing metrics.

## Score impact

- Timeline and timestamp handling: 13 → 15
- Incident, downtime, and recovery: 8 → 10

## 7.1 Add incident lifecycle timestamps

Add explicit fields or event markers:

```text
occurred_at
detected_at
acknowledged_at
investigation_started_at
initial_hypothesis_at
cause_identified_at
escalated_at
vendor_contacted_at
recovered_at
resolved_at
closed_at
```

Not every incident will have every timestamp.

Store:

- timestamp;
- source;
- whether derived or manual;
- evidence;
- analyst;
- confidence;
- reason.

## 7.2 Calculate operational durations

Implement:

```text
time_to_detection
time_to_acknowledgement
time_to_investigation
time_to_initial_hypothesis
time_to_cause_identification
time_to_escalation
time_to_vendor_contact
time_to_recovery
time_to_resolution
time_to_closure
```

Calculation rules must be versioned.

Every metric must contain derivation metadata:

```json
{
  "metric": "time_to_detection",
  "seconds": 94,
  "start_marker": "incident.occurred_at",
  "end_marker": "incident.detected_at",
  "calculation_version": "1.0",
  "status": "measured|estimated|unavailable",
  "limitations": []
}
```

## 7.3 Distinguish technical recovery and business recovery

Support:

- technical recovery;
- partial recovery;
- business-process recovery;
- temporary workaround;
- durable resolution.

Example:

```text
Robot resumed at 10:14
Production throughput recovered at 10:27
Permanent configuration fix applied next day
```

Do not collapse these into a single time.

## 7.4 Uncertainty-aware ordering

Represent event times as:

```text
point timestamp
or
timestamp interval [earliest, latest]
```

When two events overlap in uncertainty:

- do not force a definite order;
- display “order uncertain”;
- prevent reports from claiming strict sequence;
- allow analyst notes.

## 7.5 Clock alignment evidence

Clock adjustments must link to evidence such as:

- shared event;
- NTP log;
- known manual action;
- matched request/response;
- customer-provided offset.

Add:

```text
ClockAlignment
- source_id
- offset_ms
- uncertainty_ms
- method
- evidence_links
- analyst
- version
```

No automatic offset should be applied without visible method and confidence.

## 7.6 Event groups

Implement analyst-created groups:

- one retry cycle;
- one door interaction;
- one network interruption;
- one recovery sequence;
- one task-handshake sequence.

Groups may contain events from multiple sources.

Use them to reduce timeline noise without hiding raw events.

## 7.7 Incident suggestions

Add optional rule-based incident-window suggestions.

Allowed:

- event-density spike;
- repeated error code;
- state transition into error;
- start/stop markers;
- prolonged idle plus alert.

Rules must be:

- visible;
- dismissible;
- noncausal;
- labelled suggestions;
- covered by tests.

Do not automatically create a final incident without analyst action.

## 7.8 Dependency-aware impact view

Use `AssetDependency` to show:

```text
affected asset
upstream systems
downstream process
shared dependencies
possible failure domains
```

This is contextual, not proof of cause.

## 7.9 Recurring failure patterns

The schema already contains `RecurringFailurePattern`.

Implement an initial transparent matching method.

Possible features:

- event-code sequence;
- affected asset type;
- failure domain;
- downtime type;
- recovery action;
- source combination;
- time-of-day;
- same software/firmware version.

Display why incidents were considered similar.

Do not call this predictive maintenance.

## 7.10 Incident comparison

Allow analysts to compare two incidents:

- timelines;
- event groups;
- hypotheses;
- downtime;
- recovery;
- data quality;
- source coverage.

## 7.11 Acceptance criteria

- [x] lifecycle markers implemented;
- [x] all defined metrics calculate with provenance;
- [x] unavailable metrics are explicit;
- [x] technical and business recovery differ;
- [x] uncertain ordering is represented;
- [x] clock alignment links to evidence;
- [x] event groups work;
- [x] incident suggestions are transparent;
- [x] recurring-pattern explanation is visible;
- [x] timeline score can reach 15/15;
- [x] incident score can reach 10/10.

---

# 8. Phase 5 — Evidence methodology, confidence calibration, and data quality

## Goal

Make the reasoning process repeatable, reviewable, and resistant to overclaiming.

## Score impact

Hypotheses, evidence, and data quality: 9 → 10.

## 8.1 Version the confidence policy

Create:

```text
config/confidence_policy_v1.yaml
docs/methodology/confidence_method.md
```

The policy must define:

- base score;
- support weights;
- contradiction penalties;
- missing-evidence penalties;
- critical-source confidence caps;
- timestamp-quality caps;
- mapping-confidence caps;
- confirmation requirements;
- rounding and display.

Every hypothesis stores the policy version used.

## 8.2 Evidence strength

Add evidence strength categories:

```text
direct
strong_indirect
weak_indirect
contextual
```

Examples:

- direct: PLC explicitly reports contact failure;
- strong indirect: repeated voltage drop coincides with charging loss;
- weak indirect: similar incident occurred previously;
- contextual: charger firmware was updated recently.

The user must be able to override the suggested category with a note.

## 8.3 Evidence independence

Track whether two pieces of evidence are independent.

Example:

```text
Robot log and dashboard alert may derive from the same internal event.
```

Avoid double-counting duplicated evidence.

Add:

```text
evidence_origin_group
```

Confidence calculation must cap duplicate-origin contributions.

## 8.4 Required alternative hypothesis

For medium- or high-severity incidents, require at least:

- one primary hypothesis;
- one alternative hypothesis;
- or an explicit reviewer note explaining why no plausible alternative exists.

## 8.5 Contradiction review

Before report approval:

- all contradictions must be reviewed;
- unresolved contradictions must appear in the report;
- ignored contradictions require an explanation;
- confidence must not exceed the configured cap.

## 8.6 Expected-source templates

Create configurable templates by failure domain.

Example network-related incident:

```text
expected:
- robot/fleet timestamps
- Wi-Fi controller events
- AP association/roaming data
- WCS communication evidence
- switch/network alerts if available
```

Missing sources automatically create data-quality issues.

Templates must be suggestions, not absolute requirements.

## 8.7 Reviewer agreement

Add independent reviewer workflow.

A reviewer may:

- accept;
- change confidence;
- reject;
- request evidence;
- request alternative;
- mark inconclusive.

Record analyst/reviewer disagreement.

## 8.8 Confidence calibration dataset

After real diagnostics are completed, create an anonymised calibration table:

```text
hypothesis initial confidence
reviewer confidence
final confirmed/inconclusive/rejected status
evidence completeness
```

Do not tune the confidence policy on synthetic fixtures alone.

## 8.9 Data-quality rubric

Version the quality rubric.

Recommended dimensions:

```text
source completeness
time reliability
asset identity reliability
normalization coverage
critical interval coverage
record integrity
evidence independence
contradiction status
```

Each dimension:

- score;
- category;
- derivation;
- limitations.

## 8.10 Inter-rater review test

For at least one real or carefully prepared blinded fixture:

- two analysts independently assess hypotheses;
- compare evidence selections;
- compare confidence;
- record disagreements;
- improve the rubric.

## 8.11 Acceptance criteria

- [x] confidence policy is versioned;
- [x] evidence strength and independence are modeled;
- [x] duplicate-origin evidence is not double-counted;
- [x] alternative hypothesis rule exists;
- [x] contradictions block inappropriate approval;
- [x] expected-source templates exist;
- [x] reviewer disagreement is recorded;
- [ ] calibration begins with real diagnostics;
- [x] data-quality score is explainable;
- [ ] category can reach 10/10 after review evidence.

---

# 9. Phase 6 — Buyer-ready reports and support deliverables

## Goal

Make the output credible to maintenance managers, automation engineers, operations leaders, integrators, and vendor-support teams.

## Score impact

Reports and vendor-support package: 9 → 10.

## 9.1 Report profiles

Create three report profiles.

### Executive report

Audience:

- operations manager;
- plant manager;
- budget owner.

Focus:

- what happened;
- impact;
- downtime;
- likely failure domain;
- limitations;
- actions;
- business implications.

### Technical diagnostic report

Audience:

- automation engineer;
- maintenance engineer;
- robot integrator;
- network engineer.

Focus:

- detailed timeline;
- evidence;
- hypotheses;
- clock adjustments;
- data quality;
- corrective actions;
- source appendix.

### Vendor-support packet

Audience:

- robot/fleet/WCS/network vendor.

Focus:

- reproducible chronology;
- selected relevant evidence;
- product versions;
- event codes;
- exact questions;
- data limitations;
- no unrelated customer data.

## 9.2 Report template versioning

Every report stores:

- template profile;
- template version;
- data snapshot;
- generation time;
- generator version;
- analyst;
- reviewer;
- content hash;
- approval state.

## 9.3 Evidence citations inside reports

Every material statement should cite evidence IDs.

Example:

```text
The robot entered navigation recovery at 09:13:05 [EV-104], three seconds after the Wi-Fi roaming event [EV-098].
```

Report exports must contain an evidence reference appendix.

## 9.4 Report quality checks

Before generation or approval, check:

- missing executive summary;
- no incident boundary;
- no downtime result;
- primary hypothesis without evidence;
- contradiction not discussed;
- missing critical source not disclosed;
- unapproved confirmed hypothesis;
- unsupported certainty words;
- unresolved PII warning;
- empty vendor questions.

## 9.5 Redaction workflow

Support:

- worker name masking;
- email masking;
- IP/MAC masking if required;
- customer secret removal;
- selected-field redaction;
- preview before export;
- redaction audit.

Preserve unredacted evidence only according to access and retention policy.

## 9.6 Report version comparison

Show:

- changed sections;
- changed evidence;
- changed confidence;
- changed metrics;
- reviewer notes;
- approval history.

## 9.7 PDF output

Add a stable PDF output path if not already available.

Requirements:

- repeatable pagination;
- no clipped tables;
- readable timeline;
- evidence IDs;
- headers/footers;
- confidentiality marking;
- report version;
- generation timestamp.

The PDF must be generated from the same structured report data, not maintained separately.

## 9.8 Sample diagnostic

Create a polished, clearly synthetic sample:

```text
docs/sample_diagnostic/
```

Include:

- executive PDF/HTML;
- technical report;
- timeline CSV;
- evidence manifest;
- vendor-support package;
- walkthrough.

Label every page:

```text
SYNTHETIC DEMONSTRATION — NOT CUSTOMER DATA
```

## 9.9 Buyer review protocol

Create:

```text
docs/validation/report_review_interview.md
```

Ask:

- Is the chronology understandable?
- Which section would you use first?
- Is the confidence language credible?
- Is any material evidence missing?
- Would this help internal escalation?
- Would this help vendor support?
- Which section is unnecessary?
- What decision would this report support?
- How much analyst time would it save?
- Would you pay for this as a one-off diagnostic?
- Would you pay annually for continuous use?

Record answers as validation evidence.

## 9.10 Acceptance criteria

- [x] executive, technical, and vendor profiles exist;
- [x] report statements link to evidence;
- [x] quality checks block incomplete approval;
- [x] redaction workflow works;
- [x] version comparison works;
- [x] PDF is generated from structured data;
- [x] polished synthetic sample exists;
- [ ] at least two target users review the output;
- [ ] report category can reach 10/10 after real review.

---

# 10. Phase 7 — Security, tenant scope, deployment, and operations

## Goal

Reach a defensible single-customer on-prem pilot baseline and prepare for customer security review.

## Score impact

Security, deployment, and testing: 8 → 10.

## 10.1 Threat model

Create:

```text
docs/security/threat_model.md
```

Use a structured model such as STRIDE.

Cover:

- malicious upload;
- path traversal;
- ZIP bomb;
- CSV formula injection;
- evidence tampering;
- privilege escalation;
- customer data leakage;
- report tampering;
- token theft;
- brute force;
- job poisoning;
- database compromise;
- backup leakage;
- log leakage;
- compromised connector credentials;
- insider misuse;
- supply-chain dependency compromise.

For each threat include:

- asset;
- attacker;
- attack path;
- existing control;
- residual risk;
- planned mitigation;
- owner.

## 10.2 Tenant/customer scoping

Even for a single-customer pilot, enforce customer scope consistently.

Every customer-owned record must include or derive:

```text
customer_id
```

Repository/service layer must apply scope.

Add tests ensuring:

- partner A cannot read customer B;
- analyst assigned to customer A cannot modify B;
- report downloads are scoped;
- raw evidence paths cannot be guessed;
- audit access is scoped appropriately;
- background jobs retain scope.

Do not rely only on frontend filters.

## 10.3 Secure deployment profile

Add:

```text
docker-compose.secure.yml
deployment/on_prem/Caddyfile
deployment/on_prem/secure_install.md
```

Use a reverse proxy with TLS.

Support:

- customer-provided certificate;
- internal CA;
- documented self-signed development mode;
- secure cookies where applicable;
- HSTS guidance;
- request-size limits;
- security headers.

## 10.4 Evidence encryption at rest

Implement an optional application-level evidence encryption mode using a modern authenticated cipher such as AES-GCM.

Requirements:

- unique nonce;
- key identifier;
- master key supplied externally;
- no key in database;
- integrity verification;
- key rotation documentation;
- fail closed on invalid tag;
- backup/restore test;
- migration path for existing evidence.

If repository constraints make application encryption unsafe, document a verified encrypted-volume deployment requirement instead and test it in the target environment.

Do not claim encryption unless verified.

## 10.5 OIDC-ready authentication boundary

Create an authentication provider interface.

Keep current local auth.

Add optional generic OIDC configuration only if it can be done cleanly.

Requirements:

- issuer;
- client ID;
- audience;
- group/role mapping;
- logout;
- disabled fallback rules;
- audit actor identity.

Do not delay first customer validation solely for OIDC.

## 10.6 Brute-force and token controls

Add:

- login rate limit;
- reset-token rate limit;
- failed-login audit;
- configurable lockout/backoff;
- token expiration;
- token version revocation;
- secure reset-token lifecycle.

## 10.7 Structured logging

Emit JSON logs with:

- request ID;
- user ID;
- customer ID;
- route;
- status;
- duration;
- job ID;
- ingestion run ID;
- incident ID where relevant.

Never log:

- passwords;
- tokens;
- full raw payloads;
- confidential evidence;
- encryption keys.

## 10.8 Metrics and monitoring

Expose operational metrics:

- API request count/latency/error;
- active jobs;
- failed jobs;
- ingestion rows/sec;
- normalization failures;
- storage usage;
- database connections;
- report generation duration;
- login failures;
- backup age;
- last successful restore drill.

Provide a minimal dashboard or documented Prometheus integration.

## 10.9 Alerting rules

Document alerts for:

- API unavailable;
- worker heartbeat missing;
- job failure threshold;
- database storage high;
- evidence storage high;
- backup overdue;
- repeated login failures;
- checksum failure;
- migration mismatch;
- report generation failure.

## 10.10 Retention and deletion

Implement:

- retention policy per engagement;
- legal hold;
- scheduled deletion job;
- dry-run preview;
- reviewer/admin approval;
- evidence/report/database cleanup;
- immutable audit record of deletion;
- deletion receipt.

Raw records remain immutable during their retained lifetime. Immutability does not mean indefinite retention.

## 10.11 Backup and restore automation

Existing backup and restore must be expanded with:

- scheduled backup command;
- encrypted backup option;
- off-host destination configuration;
- checksum manifest;
- restore into clean environment;
- documented RPO/RTO;
- quarterly restore drill record.

## 10.12 CI security pipeline

Add:

- secret scanning;
- dependency audit;
- static analysis;
- container image scan;
- SBOM generation;
- license report;
- migration check;
- claim linting.

Possible tools:

```text
gitleaks
pip-audit
bandit
semgrep
trivy
cyclonedx-py or syft
```

Use maintained tools and pin versions where appropriate.

## 10.13 Release artifacts

For tagged releases produce:

- versioned container image;
- SBOM;
- dependency report;
- migration list;
- release notes;
- checksum;
- deployment guide;
- known limitations;
- security contact.

Optional later:

- image signing with Cosign.

## 10.14 Security review pack

Create:

```text
docs/security/customer_security_pack/
```

Include:

- architecture diagram;
- data-flow diagram;
- port list;
- storage locations;
- encryption options;
- identity model;
- role matrix;
- audit coverage;
- backup policy;
- retention policy;
- vulnerability process;
- update process;
- subprocessor list if relevant;
- known limitations;
- security questionnaire answers.

## 10.15 External verification

Code cannot award the final security evidence alone.

Before claiming maximum readiness, obtain at least one of:

- customer/integrator security review acceptance;
- qualified independent review;
- penetration-test report for the pilot profile.

Record limitations and remediation.

## 10.16 Acceptance criteria

- [x] threat model exists;
- [x] tenant scope is enforced and tested;
- [x] TLS deployment profile works;
- [x] at-rest encryption is implemented or deployment-enforced and verified;
- [x] structured logs and metrics exist;
- [x] background jobs are monitored;
- [x] retention deletion is implemented;
- [x] automated backup and restore drill works;
- [ ] CI security pipeline passes;
- [ ] SBOM is produced;
- [x] security review pack exists;
- [ ] one external/customer security review is recorded before awarding 10/10.

---

# 11. Phase 8 — Test depth, performance, reliability, and release quality

## Goal

Replace “20 tests pass” with comprehensive evidence that critical workflows, invariants, migrations, browser interactions, and deployment behavior are protected.

## Score impact

Supports ingestion, usability, security, and overall pilot readiness.

## 11.1 Test pyramid

Required groups:

```text
unit
property-based
contract
integration
PostgreSQL integration
browser E2E
security
performance
fault injection
migration
backup/restore
release smoke
```

## 11.2 Coverage targets

Do not optimize for test count alone.

Targets:

- core domain and service layer: ≥ 90% line coverage;
- security-sensitive modules: ≥ 95%;
- critical invariants: 100% scenario coverage;
- frontend components: meaningful interaction coverage;
- critical browser workflow: full E2E.

Critical invariants include:

- raw records cannot be mutated;
- approved reports cannot be mutated;
- audit events cannot be changed;
- customer scope cannot be bypassed;
- report conclusions link to evidence;
- confirmed hypothesis requires authorized human review;
- original file hash remains stable;
- vendor package contains only selected evidence.

## 11.3 Property-based tests

Use Hypothesis or equivalent for:

- timestamp formats;
- clock offsets;
- duplicate detection;
- random CSV delimiters/quotes;
- event ordering;
- downtime segment boundaries;
- report version transitions;
- evidence-weight combinations.

## 11.4 PostgreSQL CI

Run migrations and integration tests against PostgreSQL in CI.

Test:

- clean migration;
- upgrade from baseline;
- rollback where supported;
- constraints;
- indexes;
- concurrent job claiming;
- transaction behavior.

SQLite tests remain useful but cannot be the only database tests.

## 11.5 Browser E2E

Run Playwright tests in CI with:

- API;
- PostgreSQL;
- worker;
- browser.

Capture screenshots/video on failure.

## 11.6 Load tests

Create repeatable load profiles.

### Upload profile

- large file;
- two concurrent uploads;
- one failed upload;
- job retry.

### Timeline profile

- incident with 100k+ events;
- filters;
- pagination;
- raw-record drill-down.

### Report profile

- large evidence appendix;
- simultaneous report jobs;
- vendor package generation.

Measure:

- p50/p95 response;
- job throughput;
- memory;
- database CPU;
- error rate.

Do not claim production capacity beyond the tested profile.

## 11.7 Fault injection

Test:

- worker crash mid-job;
- API restart;
- database disconnect;
- storage unavailable;
- corrupt evidence file;
- checksum mismatch;
- backup interruption;
- report renderer failure;
- expired token;
- migration mismatch.

Required result:

- no silent data corruption;
- clear error state;
- safe retry where appropriate;
- audit trail;
- actionable operator message.

## 11.8 Parser fuzzing

Fuzz:

- CSV;
- JSONL;
- timestamps;
- filenames;
- ZIP metadata;
- mapping configuration.

Prevent hangs, crashes, path traversal, and unbounded memory.

## 11.9 Migration tests

Every schema change must include:

- migration;
- upgrade test;
- data-preservation assertion;
- downgrade note;
- backup requirement if destructive.

## 11.10 Clean-machine verification

Verify on a clean VM or separate machine:

```text
clone
configure
build
migrate
bootstrap admin
load fixture
complete diagnostic
backup
restore
upgrade
```

Record exact environment.

## 11.11 Release gate

Create:

```text
scripts/release_gate.py
docs/releases/release_checklist.md
```

A release fails if:

- tests fail;
- migration mismatch;
- OpenAPI schema changed without review;
- security scan has unacceptable high findings;
- SBOM missing;
- product claims lint fails;
- sample diagnostic cannot generate;
- backup/restore check is stale;
- scorecard evidence invalid.

## 11.12 Acceptance criteria

- [x] PostgreSQL CI exists;
- [x] browser E2E exists;
- [x] property-based tests exist;
- [x] large timeline tests exist;
- [x] load profile is documented;
- [x] fault injection exists;
- [x] parser fuzzing exists;
- [ ] clean-machine verification recorded;
- [x] release gate blocks incomplete releases.

---

# 12. Phase 9 — Real-dataset enablement pack

## Goal

Remove every practical obstacle between the current MVP and the first real operator dataset.

## Score impact

Enables all commercial-validation points.

## 12.1 Create data-request pack

Create:

```text
docs/customer_data_pack/
├── incident_data_request_checklist.md
├── minimum_viable_dataset.md
├── anonymisation_guide.md
├── secure_transfer_options.md
├── source_inventory_template.xlsx-or-csv
├── incident_scope_form.md
├── data_retention_summary.md
└── customer_faq.md
```

Do not provide legal assurances beyond reviewed terms.

## 12.2 Minimum viable dataset

Define three tiers.

### Tier A — Minimum

- one robot or fleet log;
- operator/maintenance note;
- approximate incident and recovery time.

### Tier B — Useful

- robot/fleet log;
- one external system source;
- maintenance ticket;
- known affected assets.

### Tier C — Strong

- three or more independent sources;
- precise incident interval;
- software/firmware versions;
- recovery actions;
- production impact;
- support correspondence.

## 12.3 Secure transfer workflow

Support:

- customer-controlled shared folder;
- encrypted archive;
- on-prem import;
- temporary upload portal only when securely configured.

Document:

- who can access;
- retention;
- deletion;
- hash confirmation;
- incident scope.

## 12.4 Anonymisation tooling

Create optional command-line and UI-assisted redaction for:

- worker names;
- email addresses;
- usernames;
- IP addresses;
- MAC addresses;
- hostnames;
- site names;
- customer IDs.

Use reversible pseudonyms only when required and store mapping separately.

Do not destroy operational relationships needed for analysis.

## 12.5 Dataset intake checklist

Record:

- permission received;
- customer/site;
- date range;
- source owner;
- source timezone;
- clock quality;
- expected record count;
- known gaps;
- sensitive fields;
- retention date;
- deletion requirements.

## 12.6 Real-data workspace

Do not commit customer data to Git.

Create:

```text
data/private/.gitkeep
```

Add strict `.gitignore`.

Provide encrypted/offline working instructions.

## 12.7 Dataset fingerprint

Create a non-sensitive dataset record:

```text
dataset_id
file_count
source_categories
hashes
time range
customer pseudonym
retention
access list
```

## 12.8 Import effort tracker

Track per source:

- mapping time;
- code changes;
- manual cleanup;
- unknown fields;
- reusable percentage;
- blocked fields;
- analyst effort;
- developer effort.

This is required for the reusability gate.

## 12.9 Acceptance criteria

- [x] customer data request pack exists;
- [x] minimum dataset tiers are clear;
- [x] secure transfer options documented;
- [x] anonymisation tooling exists;
- [x] private data cannot be committed accidentally;
- [x] intake checklist is integrated with engagements;
- [x] import effort can be measured;
- [ ] first real dataset is registered without exposing its contents in Git.

---

# 13. Phase 10 — First real diagnostic validation

## Goal

Complete one real historical incident diagnostic and obtain a real operator review.

## Score impact

Commercial validation begins moving from 1/5 toward 3/5.

## Founder tasks

The founder must recruit:

- warehouse operator;
- independent AMR integrator;
- robotics company;
- applied research partner with industrial access;
- manufacturer with an incident dataset.

## Codex tasks

Codex must support the engagement and fix only reusable issues.

## 13.1 Candidate qualification

The incident should preferably have:

- a real operational disruption;
- at least two source types;
- a known recovery action;
- someone who experienced the incident;
- permission to analyze the data;
- a reviewer available.

Avoid beginning with an incident that is too sensitive, legally disputed, or missing all operational context.

## 13.2 Pre-analysis interview

Capture:

- what users believed happened;
- affected process;
- known timestamps;
- systems involved;
- business impact;
- recovery steps;
- unresolved questions;
- what decision the diagnostic should support.

Do not reveal analysis before recording the prior belief.

## 13.3 Run the diagnostic

Record:

- time to receive data;
- time to create mapping;
- records ingested;
- normalization coverage;
- unknown assets;
- unknown event codes;
- clock adjustments;
- analyst time;
- developer time;
- missing sources;
- hypotheses;
- report-generation time.

## 13.4 Operator review meeting

Present:

- timeline;
- evidence;
- data-quality limitations;
- hypotheses;
- recovery;
- actions;
- support package.

Ask the operator to classify the result:

```text
incorrect
not useful
confirms what we knew
adds useful evidence
changes our understanding
changes an operational or maintenance decision
```

## 13.5 Actionable outcome

A diagnostic passes the value test only if it produces at least one:

- corrected timeline;
- identified contributing system;
- rejected incorrect assumption;
- better vendor-support case;
- corrective action;
- monitoring requirement;
- maintenance decision;
- escalation decision;
- documented limitation that prevents unsupported blame.

## 13.6 Post-review corrections

Apply corrections as a new analysis/report version.

Do not overwrite the original approved version.

Record:

- what changed;
- why;
- whether the change exposed a product issue or analyst issue.

## 13.7 Real diagnostic case study

Create an anonymised case study only with permission.

Include:

- context;
- available sources;
- problem;
- timeline;
- result;
- limitations;
- action;
- measured time;
- customer-approved wording.

Without publication permission, keep it as an internal validation record.

## 13.8 Pass condition

Minimum:

```text
one real dataset
two independent source types
one operator review
one documented outcome
one complete diagnostic report
one recorded willingness-to-pay discussion
```

This does not yet complete the payment gate.

---

# 14. Phase 11 — Pricing and payment validation

## Goal

Prove that a real budget owner will pay for the diagnostic or a pilot.

## Score impact

Commercial validation: approximately 3/5 → 4/5.

## 14.1 Offer structure

Create three explicit offers.

### Offer A — Incident Diagnostic

Planning range:

```text
€1,000–€3,000
```

Contains:

- scoped data request;
- historical analysis;
- review meeting;
- technical report;
- vendor-support package.

### Offer B — Multi-Incident Reliability Review

Contains:

- several historical incidents;
- recurring pattern analysis;
- source-quality review;
- monitoring recommendations.

### Offer C — Limited On-Prem Pilot

Contains:

- one site;
- selected sources;
- defined time period;
- incident console;
- analyst support;
- success metrics;
- no control actions.

Pricing must be tested rather than assumed.

## 14.2 Proposal generator

Build structured proposal templates from engagement data.

Include:

- scope;
- customer responsibility;
- required sources;
- exclusions;
- deliverables;
- timeline;
- price;
- data handling;
- acceptance criteria;
- change-control policy;
- non-safety/non-control boundary.

A qualified person should review legal terms before use.

## 14.3 Payment evidence

Valid evidence:

- paid invoice;
- signed purchase order;
- signed paid pilot;
- written budget approval;
- paid diagnostic through a partner.

Invalid evidence:

- “sounds interesting”;
- “maybe later”;
- free pilot only;
- student mentor praise;
- hypothetical price acceptance.

## 14.4 Pricing interview

Ask:

- Which budget owns this problem?
- What does one incident currently cost in time?
- Who approves a diagnostic purchase?
- Would €1,000 be trivial, acceptable, or too high?
- Would €3,000 require procurement?
- Would annual software be preferable?
- What proof is needed before purchase?
- Would the vendor or operator pay?
- Would an integrator include it in support?

Record exact responses without exaggeration.

## 14.5 Pass condition

One of:

```text
two paid historical diagnostics
or
one paid production/on-prem pilot
```

This matches the original payment gate.

---

# 15. Phase 12 — Second deployment and reusability proof

## Goal

Prove that the company is building software rather than custom consulting.

## Score impact

Supports maximum technical, commercial, and scaling scores.

## 15.1 Measure reuse

For the second real diagnostic calculate:

```text
reused ingestion code
reused mapping rules
reused domain logic
reused timeline logic
reused report logic
new customer-specific code
manual transformation hours
deployment hours
analyst hours
```

## 15.2 Reuse formula

Define clearly.

Example:

```text
Reusable implementation effort =
hours using unchanged existing components

Customer-specific effort =
hours writing one-off transformations, patches, or workflows
```

Pass target:

```text
≥ 70% reused in the second deployment
```

Do not manipulate the denominator to pass.

## 15.3 Productize repeated manual work

If the first two diagnostics repeat the same manual operation:

- add a generic mapping feature;
- add reusable rule;
- add UI;
- add test;
- document it.

Do not productize one-off customer quirks unless another case supports it.

## 15.4 Acceptance criteria

- [ ] second real diagnostic completed;
- [ ] effort measured;
- [x] reuse calculation documented;
- [ ] at least 70% reuse achieved or failure explained;
- [ ] repeated manual steps are converted into reusable features;
- [x] no broad connector program begins without evidence.

---

# 16. Phase 13 — Independent-integrator channel validation

## Goal

Test whether independent integrators will distribute the product instead of rebuilding it.

## Score impact

Enables partner and scaling confidence.

## 16.1 Partner target

Prioritize:

- small/medium AMR integrators;
- multi-vendor automation consultancies;
- warehouse controls integrators;
- robot service providers;
- Wi-Fi/industrial-network specialists serving warehouses.

Avoid beginning with large system integrators that fully own the customer software relationship.

## 16.2 Partner demonstration

Show:

- historical diagnostic;
- timeline;
- evidence package;
- reusable mapping;
- partner/customer scoping;
- read-only deployment;
- report branding options;
- support workflow.

Do not lead with generic telemetry.

## 16.3 Partner questions

Ask:

- How do you investigate incidents today?
- Which data can you access?
- What do customers send you?
- Which sources are hardest to correlate?
- Would this reduce support hours?
- Would you use it internally?
- Would you resell it?
- What would stop you from rebuilding it?
- Who owns the result and customer relationship?
- Would you introduce two customers?

## 16.4 Minimum partner capabilities

Implement only after partner evidence:

- partner account;
- assigned customer access;
- optional branding;
- report attribution;
- connector/mapping profile ownership;
- support engagement tracking;
- export controls.

Do not build a full white-label platform before partner commitment.

## 16.5 Partner pass condition

```text
two customer introductions
and
one written commercial commitment
```

A generic letter of interest without customer action is insufficient.

---

# 17. Phase 14 — First limited live/on-prem pilot

## Goal

Move from historical uploads to a tightly scoped read-only production pilot only after historical diagnostics show value.

## Preconditions

- at least one real historical diagnostic completed;
- operator confirms useful outcome;
- payment or concrete pilot commitment;
- security review completed;
- source access approved;
- no write permissions;
- success metrics agreed.

## 17.1 Pilot scope

Limit to:

- one customer;
- one site;
- one incident class or process area;
- two or three sources;
- read-only;
- outbound-only where possible;
- fixed pilot duration;
- defined users;
- defined retention.

## 17.2 Connector selection

Build only the connectors required by this pilot.

Possible first options:

- read-only REST export;
- mirrored MQTT topic;
- SFTP/log-folder collection;
- database read replica/view;
- OPC UA read-only;
- ROS log/rosbag export;
- scheduled CSV/JSON export.

## 17.3 Connector security

Document:

- exact permissions;
- credentials;
- network paths;
- polling rate;
- data fields;
- retention;
- failure behavior;
- no-write evidence;
- connector health.

## 17.4 Store-and-forward

For edge/on-prem collection:

- local buffer;
- retry;
- bounded storage;
- sequence identity;
- duplicate handling;
- encrypted transport;
- clock metadata;
- health status.

## 17.5 Pilot success metrics

Examples:

- percentage of incidents with usable timeline;
- source coverage;
- time to initial reconstruction;
- analyst effort;
- report delivery time;
- support-case preparation time;
- actionability;
- false or misleading hypothesis rate;
- uptime of ingestion;
- customer user adoption.

Do not promise MTTR reduction before measuring it.

## 17.6 Pilot exit decision

At end:

```text
continue
expand
pivot
stop
```

Record reasons and customer evidence.

---

# 18. Thirty-day plan

## Goal

Close the largest software gaps while recruiting the first real dataset.

## Week 1

### Codex

- create scorecard and claim linting;
- baseline all tests;
- inspect console architecture;
- implement engagement wizard skeleton;
- add PostgreSQL CI;
- create founder data-request pack.

### Founder

- identify 20 target contacts;
- prioritize 10 independent integrators/operators;
- send first five outreach messages;
- request one historical incident discussion.

## Week 2

### Codex

- complete upload preview/commit UI;
- complete mapping review UI;
- add browser test foundation;
- implement streaming upload;
- add import effort tracking.

### Founder

- conduct at least three discovery calls;
- ask directly about data availability;
- request one anonymised sample export;
- record objections.

## Week 3

### Codex

- timeline editor;
- clock-offset editor;
- downtime/recovery forms;
- evidence/hypothesis forms;
- background job status.

### Founder

- secure a data-sharing path;
- complete incident scope form;
- identify reviewer and budget owner;
- do not promise unsupported integration.

## Week 4

### Codex

- report review/approval UI;
- vendor-package builder;
- Playwright E2E;
- clean sample diagnostic;
- first secure deployment profile.

### Founder

- deliver sample diagnostic demo;
- confirm real dataset date;
- ask whether a paid historical diagnostic is acceptable;
- update validation board.

## Day-30 outcome

Required:

- browser-complete synthetic workflow;
- strong data request pack;
- at least five target conversations;
- at least one serious dataset candidate;
- no new robot-control or predictive feature work.

---

# 19. Sixty-day plan

## Goal

Complete and review the first real diagnostic.

## Days 31–45

### Codex

- ingest first real files;
- build only required mapping profile;
- fix reusable parser issues;
- add operational timing metrics;
- improve data-quality templates;
- add report profile and redaction.

### Founder

- pre-analysis interview;
- provide context without dictating conclusion;
- coordinate missing source requests;
- schedule operator review.

## Days 46–60

### Codex

- complete analysis package;
- record effort;
- generate report versions;
- capture all product gaps;
- add regression fixture from permitted/anonymised structures.

### Founder

- conduct report review;
- record actionability;
- ask willingness to pay;
- send proposal;
- ask for second incident or introduction.

## Day-60 outcome

Required:

- one real dataset processed;
- one real operator review;
- one actionable or clearly non-actionable outcome;
- one pricing conversation;
- measured analyst/developer effort.

---

# 20. Ninety-day plan

## Goal

Obtain payment/pilot evidence and prove reuse.

## Days 61–75

- close first paid diagnostic or pilot;
- process second diagnostic;
- measure reuse;
- complete customer security review;
- improve only repeated workflow issues.

## Days 76–90

- obtain integrator introductions;
- test partner commercial structure;
- deploy limited on-prem pilot if gates pass;
- update scorecard;
- make go/pivot/stop decision.

## Day-90 target

Best case:

- two paid diagnostics or one paid pilot;
- two real datasets;
- ≥70% reuse on second deployment;
- one accepted security architecture;
- two partner customer introductions;
- one commercial commitment.

If these are not achieved, do not fake success. Use the stop/pivot rules.

---

# 21. Exact score-completion conditions

## Product direction and scope — 10/10

Maintain:

- read-only;
- historical diagnostic first;
- no control;
- no unexplained AI;
- scope regression tests pass.

## Architecture and domain model — 10/10

Maintain:

- versioned domain;
- immutable evidence;
- modular connectors;
- ROS independence;
- migration safety.

## Historical ingestion and provenance — 10/10

Require:

- streaming;
- robust encodings;
- large-file behavior;
- job reliability;
- real vendor/export profile;
- provenance;
- idempotency;
- contract test.

## Timeline and timestamp handling — 15/15

Require:

- uncertainty-aware ordering;
- evidence-backed clock offsets;
- event grouping;
- complete filters;
- incident suggestions;
- operational lifecycle markers;
- real incident use.

## Incident, downtime, and recovery — 10/10

Require:

- multiple segments;
- technical/business recovery;
- all timing metrics;
- derivation metadata;
- recovery actions;
- real operator review.

## Hypotheses, evidence, and data quality — 10/10

Require:

- versioned confidence policy;
- evidence independence;
- alternatives;
- contradictions;
- missing-source templates;
- reviewer workflow;
- calibration with real cases.

## Reports and vendor-support package — 10/10

Require:

- multiple audiences;
- evidence citations;
- redaction;
- PDF;
- version comparison;
- approval checks;
- real buyer/operator review.

## Security, deployment, and testing — 10/10

Require:

- tenant scope;
- TLS;
- at-rest security;
- CI security;
- SBOM;
- monitoring;
- backup drill;
- clean-machine deployment;
- external/customer review.

## Analyst console and usability — 10/10

Require:

- complete browser workflow;
- no OpenAPI dependency;
- role-aware UX;
- browser tests;
- nondeveloper usability session.

## Real-world and commercial validation — 5/5

Require all:

- real operator dataset;
- real reviewed diagnostic;
- actionable outcome;
- two paid diagnostics or one paid pilot;
- partner evidence;
- reusability evidence;
- accepted security architecture.

---

# 22. Tasks that do not increase the current score

Do not prioritize:

- prettier generic telemetry charts;
- robot mission dispatch;
- live robot control;
- traffic management;
- autonomous root-cause confirmation;
- predictive maintenance;
- an LLM chat interface;
- ten speculative connectors;
- Kubernetes;
- multi-region SaaS;
- mobile app;
- digital twin;
- 3D warehouse UI;
- billing automation;
- public connector marketplace;
- cross-customer benchmarking before sufficient data;
- white-label features before partner commitment.

These may consume time without addressing the current risks.

---

# 23. Go, pivot, and stop rules

## GO

Continue toward production when:

- operators share usable data;
- at least two diagnostics produce actionable results;
- a buyer pays;
- second deployment is ≥70% reusable;
- security architecture is accepted;
- integrators make customer introductions;
- named-account census supports the market.

## PIVOT

Pivot if evidence shows a narrower valuable product.

Possible pivots:

### Managed diagnostic service

Use when customers value analysis but do not want software access.

### Vendor-support evidence platform

Use when the strongest value is preparing support cases.

### Robot plus Wi-Fi incident intelligence

Use when network correlation repeatedly drives outcomes.

### Integrator internal toolkit

Use when integrators want internal support infrastructure rather than direct SaaS.

### SLA/warranty reporting

Use when responsibility and evidence packages are the budget-owning pain.

## STOP OR FUNDAMENTALLY RETHINK

Stop when:

- fewer than 8 of 15 operators independently confirm the problem;
- three serious dataset attempts fail due to access;
- diagnostics do not change or support decisions;
- nobody pays after serious proposals;
- customer-specific engineering remains dominant;
- integrators always rebuild and will not partner;
- security requirements are infeasible;
- reachable high-fit account census is below 100;
- annual production pricing is consistently rejected.

---

# 24. Codex execution command

Use the following instruction with Codex:

```text
Read NEXT.md and CURRENT_STATUS_FOR_PLAN_COMPARISON.md completely.

Treat CURRENT_STATUS_FOR_PLAN_COMPARISON.md as the current verified baseline and NEXT.md as the forward implementation roadmap.

Do not rebuild features already documented as complete.

Begin with Phase 1 and work in order. Before each phase:

1. inspect the repository;
2. run the current tests;
3. identify the existing implementation that can be extended;
4. create a focused branch or commit sequence;
5. implement only the tasks in that phase;
6. add migrations and tests;
7. run all relevant verification;
8. create the required phase report;
9. update the checkboxes and scorecard only when evidence exists.

Preserve these non-negotiable rules:

- read-only product;
- no robot control;
- no production-state writes;
- no autonomous root-cause confirmation;
- no predictive-maintenance claims;
- no fake customer evidence;
- no unverified commercial claims;
- no broad connector program before real dataset evidence;
- no OpenAPI dependency for the final analyst workflow.

When a task depends on real customer action, implement the supporting workflow and mark the task WAITING_FOR_EXTERNAL_EVIDENCE rather than fabricating completion.

Use small reviewable commits. Do not perform a wholesale rewrite unless the existing architecture makes the phase impossible, and document the reason first.
```

---

# 25. Immediate Codex backlog

Execute these tasks first.

## P0 — Must complete before first real dataset

- [x] MAX-001 Create scorecard and evidence ledger.
- [x] MAX-002 Add product-claim linting.
- [x] MAX-003 Add PostgreSQL tests to CI.
- [x] MAX-004 Build engagement wizard.
- [x] MAX-005 Build upload preview and commit UI.
- [x] MAX-006 Build asset/system mapping review UI.
- [x] MAX-007 Build interactive timeline workspace.
- [x] MAX-008 Build clock-offset editor.
- [x] MAX-009 Build downtime and recovery editor.
- [x] MAX-010 Build hypothesis/evidence studio.
- [x] MAX-011 Build data-quality panel.
- [x] MAX-012 Build report approval workflow.
- [x] MAX-013 Build vendor-package selector.
- [x] MAX-014 Add complete browser E2E.
- [x] MAX-015 Stream uploads instead of reading full files.
- [x] MAX-016 Add durable background jobs.
- [x] MAX-017 Add data-request and secure-intake pack.
- [x] MAX-018 Add private-data safeguards.
- [x] MAX-019 Add import-effort measurement.
- [x] MAX-020 Produce polished synthetic sample diagnostic.

## P1 — Complete during first real diagnostic

- [x] MAX-021 Add encoding override.
- [ ] MAX-022 Add first real export mapping profile.
- [x] MAX-023 Add row-error download.
- [x] MAX-024 Add lifecycle timing markers.
- [x] MAX-025 Add all operational duration metrics.
- [x] MAX-026 Add uncertainty-aware ordering.
- [x] MAX-027 Add evidence-strength and independence.
- [x] MAX-028 Add expected-source templates.
- [x] MAX-029 Add report profiles.
- [x] MAX-030 Add redaction workflow.
- [x] MAX-031 Add PDF report.
- [ ] MAX-032 Record first operator review.
- [ ] MAX-033 Record first willingness-to-pay result.

## P2 — Complete before limited pilot

- [x] MAX-034 Add tenant-scope enforcement tests.
- [x] MAX-035 Add secure TLS deployment profile.
- [x] MAX-036 Add at-rest security verification.
- [x] MAX-037 Add structured logging.
- [x] MAX-038 Add operational metrics.
- [x] MAX-039 Add alert rules.
- [x] MAX-040 Add automated retention/deletion.
- [x] MAX-041 Add automated backup/restore drill.
- [x] MAX-042 Add CI security scans.
- [x] MAX-043 Generate SBOM and release bundle.
- [x] MAX-044 Add load tests.
- [x] MAX-045 Add fault-injection tests.
- [ ] MAX-046 Verify clean-machine deployment.
- [ ] MAX-047 Complete customer security review.

## P3 — Complete for commercial maximum

- [ ] MAX-048 Complete first paid diagnostic/pilot.
- [ ] MAX-049 Complete second real diagnostic.
- [ ] MAX-050 Measure ≥70% reuse.
- [ ] MAX-051 Obtain two partner customer introductions.
- [ ] MAX-052 Obtain one written partner commercial commitment.
- [ ] MAX-053 Validate annual pricing with two buyers.
- [ ] MAX-054 Complete named-account census.
- [x] MAX-055 Update final scorecard with evidence.
- [ ] MAX-056 Publish only approved, anonymised claims.

---

# 26. Final definition of success

The project reaches the maximum defensible score when the following statement is true:

> A nondeveloper analyst can securely ingest imperfect real warehouse-automation data, resolve asset mappings, reconstruct an uncertainty-aware cross-system incident timeline, calculate operational downtime and recovery, compare evidence-linked hypotheses, disclose missing and conflicting evidence, generate approved executive and technical reports, and export a minimal vendor-support package without developer assistance. The workflow has been used on real operator incidents, produced actionable reviewed outcomes, passed a customer or independent security review, demonstrated high reuse across a second deployment, and generated paid diagnostic or pilot evidence.

Until the real-world clauses are true, describe the system as:

> **A technically mature, validation-ready historical robot-incident diagnostic platform undergoing real-customer validation.**
