# NEXT.md — Convert the Existing ROS 2 Inspection Repository into the Robot Fleet Incident Intelligence Startup

**Document purpose:**  
This file is the implementation handoff for Codex or another engineering agent.

The current repository is a strong ROS 2 + Nav2 autonomous inspection prototype. We will make a full copy of that repository and convert the copied repository into the first validation-ready version of the startup:

> **A read-only incident and reliability intelligence layer for brownfield warehouses and factories. It ingests exported or live data from robots, fleet systems, WMS/WCS, PLCs, chargers, doors, lifts and network systems; normalises events; reconstructs incidents; measures downtime and recovery; evaluates evidence quality; and generates traceable maintenance and vendor-support reports.**

The first commercial product is **not** a generic fleet dashboard and **not** a robot-control platform.

The first commercial product is:

> **Historical Robot Incident Diagnostic**  
> A paid diagnostic engagement using exported logs, tickets, CSV/JSON files and other available evidence to reconstruct a real warehouse-robot incident and produce an actionable evidence package.

---

# 1. Non-Negotiable Product Direction

## 1.1 The copied repository must become a separate product

Do not continue developing the copied repository primarily as an autonomous inspection robot platform.

The original repository remains the autonomous inspection and simulation project.

The copied repository becomes the incident-intelligence startup product.

Recommended naming:

```text
Original repository:
factory_inspection_robot

Copied startup repository:
robot_fleet_incident_intelligence
```

Alternative startup names are acceptable, but the architecture must reflect the new product.

---

## 1.2 The startup product must be read-only

The startup must not initially:

- send navigation goals
- allocate missions
- control robots
- stop or start production systems
- change PLC values
- modify WMS/WCS state
- perform fleet traffic management
- send safety commands
- replace a fleet manager
- replace a WMS/WES/WCS
- act as an autonomous root-cause decision-maker

The product may:

- ingest files
- ingest read-only APIs
- receive mirrored MQTT events
- read ROS topics or bags
- read OPC UA values using read-only credentials
- read logs
- correlate events
- reconstruct timelines
- calculate downtime
- generate hypotheses
- show confidence and missing evidence
- create reports
- export vendor-support packages
- track human investigation and corrective actions

---

## 1.3 The initial buyer problem

The first buyer problem is:

> “A robot or automation process stopped. Information is spread across several systems. The team spends too much time collecting evidence, comparing timestamps, deciding responsibility and preparing a vendor-support case.”

The product must reduce:

- time to collect evidence
- time to reconstruct an incident
- time to identify the most likely failure domain
- time to prepare a support case
- repeated manual analysis of recurring incidents
- uncertainty caused by missing or contradictory data

The product must not be described as:

> “A dashboard that collects robot telemetry.”

---

# 2. Final Product Scope

## 2.1 Primary startup product

The production concept is:

```text
Read-only data ingestion
        ↓
Raw evidence preservation
        ↓
Canonical event normalisation
        ↓
Asset and system mapping
        ↓
Timestamp alignment
        ↓
Incident reconstruction
        ↓
Downtime and recovery calculation
        ↓
Evidence and data-quality analysis
        ↓
Root-cause hypothesis support
        ↓
Maintenance and vendor-support report
```

---

## 2.2 First commercial offer

### Historical Robot Incident Diagnostic

Expected pricing target:

```text
€1,000–€3,000 per diagnostic
```

Input examples:

- robot logs
- fleet-manager exports
- WMS/WCS exports
- PLC alarms
- Wi-Fi controller logs
- maintenance tickets
- operator notes
- screenshots
- support emails
- CSV files
- JSON files
- ROS logs
- rosbag-derived events

Output:

- executive incident summary
- chronological cross-system timeline
- affected systems and assets
- downtime calculation
- recovery sequence
- most likely failure domain
- alternative hypotheses
- supporting evidence
- contradicting evidence
- missing evidence
- data-quality limitations
- recommended next actions
- vendor-support evidence package
- analyst-approved final report

---

## 2.3 Later product stages

Only after real validation:

### Stage 2

```text
Production incident-intelligence platform
```

### Stage 3

```text
White-label toolkit for independent robot and automation integrators
```

### Stage 4

Possible later capabilities:

- CMMS/EAM integration
- VDA 5050 observability
- WMS/WES plug-ins
- edge appliance
- connector SDK
- recurring-failure intelligence
- warranty and SLA reporting
- AI-assisted root-cause review
- predictive maintenance

Do not implement Stage 4 before the validation gates in this document are passed.

---

# 3. Required Repository Strategy

## 3.1 Preserve the current working system

The current project already contains valuable components:

- ROS 2 architecture
- Gazebo benchmark
- Nav2 integration
- site configuration
- asset registry
- inspection profiles
- findings
- evidence
- SQLite persistence
- FastAPI operator API
- operator console
- JSON, CSV, Markdown and HTML reports
- schema versioning
- mission identity and traceability

Do not delete these components immediately.

Move or adapt them.

---

## 3.2 Target repository structure

Refactor the copied repository toward this structure:

```text
robot_fleet_incident_intelligence/
├── README.md
├── NEXT.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── Makefile
│
├── docs/
│   ├── product/
│   │   ├── product_definition.md
│   │   ├── scope_and_non_goals.md
│   │   ├── terminology.md
│   │   └── commercial_offer.md
│   ├── architecture/
│   │   ├── system_architecture.md
│   │   ├── data_flow.md
│   │   ├── security_architecture.md
│   │   └── deployment_architecture.md
│   ├── schemas/
│   ├── diagnostics/
│   ├── validation/
│   └── phase_reports/
│
├── apps/
│   ├── diagnostic_api/
│   ├── operator_console/
│   └── report_worker/
│
├── packages/
│   ├── domain_models/
│   ├── ingestion_core/
│   ├── connector_sdk/
│   ├── event_normalization/
│   ├── asset_mapping/
│   ├── timeline_engine/
│   ├── incident_engine/
│   ├── data_quality/
│   ├── reliability_metrics/
│   ├── hypothesis_engine/
│   ├── report_generation/
│   ├── audit/
│   └── common/
│
├── connectors/
│   ├── generic_csv/
│   ├── generic_json/
│   ├── jsonl/
│   ├── ros_logs/
│   ├── rosbag_export/
│   ├── maintenance_ticket/
│   ├── wifi_logs/
│   └── mock_sources/
│
├── autonomy_demo/
│   ├── ros2_ws/
│   ├── simulation_scenarios/
│   └── synthetic_exporters/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── security/
│   ├── regression/
│   └── end_to_end/
│
├── fixtures/
│   ├── incident_001_door_wifi/
│   ├── incident_002_charger/
│   ├── incident_003_wcs_delay/
│   └── malformed_sources/
│
├── deployment/
│   ├── docker/
│   ├── on_prem/
│   └── migrations/
│
└── validation/
    ├── interviews/
    ├── datasets/
    ├── diagnostics/
    ├── proposals/
    ├── partner_discussions/
    └── confidence_board/
```

---

## 3.3 Migration rules

Codex must follow these rules:

1. Keep the original benchmark working while the new product is created.
2. Do not rewrite everything at once.
3. Move reusable code only after tests exist.
4. Introduce database migrations before changing persistent schemas.
5. Preserve schema versions.
6. Add compatibility adapters where necessary.
7. Do not claim support for a source that is only represented by synthetic data.
8. Do not create fake customer names, fake commercial validation or fake production metrics.
9. Use synthetic fixtures for development.
10. Clearly label benchmark, simulated and real-data functionality.
11. The new incident workflow must work without starting ROS, Gazebo or Nav2.
12. The ROS/Gazebo stack becomes an optional data generator and demo environment.

---

# 4. Phase 0 — Copy, Freeze and Baseline the Repository

## Goal

Create a safe copy and prove that the current benchmark still works before conversion.

## Tasks

### 4.1 Create the copied repository

```bash
cp -a <current_repo> robot_fleet_incident_intelligence
cd robot_fleet_incident_intelligence
git init
git add .
git commit -m "Baseline copied autonomous inspection repository"
```

If the copy already has Git history, preserve the history and create a new remote.

### 4.2 Create a conversion branch

```bash
git checkout -b startup-incident-intelligence
```

### 4.3 Add a baseline tag

```bash
git tag pre-conversion-baseline
```

### 4.4 Record current functionality

Create:

```text
docs/phase_reports/phase_00_conversion_baseline.md
```

Include:

- current launch commands
- current API startup command
- current UI startup command
- current test commands
- existing database location
- generated artifact locations
- screenshots or evidence
- known failures
- exact commit hash

### 4.5 Run existing verification

Verify at minimum:

- repository builds
- benchmark launches
- Nav2 activates
- one patrol round executes
- one finding is generated
- one operator mission can be created
- SQLite state is written
- JSON and HTML reports are generated

### Acceptance criteria

- existing benchmark runs from the copied repository
- current tests pass or known failures are documented
- no new startup code is written before baseline completion
- baseline commit and tag exist

---

# 5. Phase 1 — Product Repositioning and Terminology

## Goal

Prevent the copied repository from continuing in the wrong product direction.

## 5.1 Create product-definition documents

Create:

```text
docs/product/product_definition.md
docs/product/scope_and_non_goals.md
docs/product/terminology.md
docs/product/commercial_offer.md
```

### product_definition.md must contain

- target user
- target buyer
- target incident
- pain statement
- input sources
- expected outputs
- why the product is read-only
- difference from fleet management
- difference from telemetry dashboards
- difference from predictive maintenance
- difference from robot inspection

### scope_and_non_goals.md must explicitly reject

- robot control
- traffic management
- fleet orchestration
- mission planning
- WMS replacement
- generic observability
- predictive maintenance
- digital twin
- autonomous safety decisions
- unreviewed AI conclusions

### terminology.md must define

- source
- raw record
- canonical event
- asset
- system
- incident
- downtime
- recovery
- evidence
- hypothesis
- finding
- corrective action
- support case
- diagnostic engagement
- analysis run
- data-quality issue
- confidence

## 5.2 Rename product-facing concepts

Do not reuse names in ways that create confusion.

Recommended mapping:

```text
Old concept              New product equivalent
-------------------------------------------------------
Mission                   Diagnostic engagement
Mission report            Diagnostic report
Round                     Analysis run
Inspection result         Event or finding
Checkpoint                Asset or process stage
Mission queue             Ingestion/analysis job queue
Campaign state            Incident/reliability history
FleetWatch                Incident Console
```

Do not remove old concepts from the autonomy demo. Rename only the new startup-facing product layer.

### Acceptance criteria

- README describes incident intelligence first
- autonomy inspection is described as a demo/data generator
- product and non-goals are explicit
- no main product page presents robot control as the startup offer

---

# 6. Phase 2 — Core Domain Model

## Goal

Create the correct data model before implementing connectors or AI.

## 6.1 Required entities

Implement versioned domain models for:

```text
Customer
Site
Area
System
Asset
AssetDependency
DataSource
Connector
IngestionRun
RawRecord
CanonicalEvent
DataQualityIssue
Incident
IncidentAsset
TimelineEntry
DowntimeSegment
RecoveryAction
RootCauseHypothesis
EvidenceLink
Finding
CorrectiveAction
MaintenanceWorkOrder
Vendor
SupportCase
RecurringFailurePattern
DiagnosticEngagement
AnalysisRun
ReportArtifact
AuditEvent
User
Role
```

## 6.2 Required identifiers

Use UUIDs internally.

Every imported object must retain source identity:

```text
source_record_id
external_asset_id
external_system_id
source_filename
source_line_number
source_timestamp
ingested_at
ingestion_run_id
schema_version
```

## 6.3 Raw record requirements

A raw record must be immutable after ingestion.

Required fields:

```json
{
  "id": "uuid",
  "ingestion_run_id": "uuid",
  "data_source_id": "uuid",
  "source_record_id": "string-or-null",
  "source_filename": "string-or-null",
  "source_line_number": 42,
  "source_timestamp_raw": "original value",
  "payload": {},
  "payload_sha256": "hash",
  "ingested_at": "ISO-8601",
  "schema_version": "1.0"
}
```

## 6.4 Canonical event requirements

Required fields:

```json
{
  "id": "uuid",
  "raw_record_id": "uuid",
  "event_type": "robot.error",
  "event_code": "LOCALIZATION_LOST",
  "event_time": "ISO-8601 UTC",
  "event_time_original": "source value",
  "time_quality": "exact|converted|estimated|unknown",
  "clock_offset_ms": 0,
  "severity": "info|warning|error|critical|unknown",
  "system_id": "uuid-or-null",
  "asset_id": "uuid-or-null",
  "message": "string",
  "state_from": "string-or-null",
  "state_to": "string-or-null",
  "attributes": {},
  "normalizer_version": "string",
  "schema_version": "1.0"
}
```

## 6.5 Incident requirements

Required fields:

```json
{
  "id": "uuid",
  "diagnostic_engagement_id": "uuid",
  "site_id": "uuid",
  "title": "string",
  "description": "string",
  "status": "open|investigating|review|resolved|closed",
  "started_at": "ISO-8601",
  "recovered_at": "ISO-8601-or-null",
  "downtime_seconds": 0,
  "business_impact": "string-or-null",
  "created_by": "uuid",
  "approved_by": "uuid-or-null",
  "confidence": 0.0,
  "schema_version": "1.0"
}
```

## 6.6 Evidence relationship

Evidence must never be represented only as free text.

Implement:

```text
EvidenceLink
- incident_id
- hypothesis_id
- canonical_event_id or raw_record_id or report_artifact_id
- relation:
    supports
    contradicts
    contextual
    missing_expected
- analyst_note
- weight
- created_by
- created_at
```

## 6.7 Data-quality issue model

Support:

- missing expected source
- missing time range
- unparseable timestamp
- clock drift
- duplicate event
- ambiguous asset mapping
- unknown event code
- impossible ordering
- stale source
- incomplete export
- corrupted file
- conflicting records
- unsupported format

## 6.8 Persistence

Use PostgreSQL for the target architecture.

SQLite may remain available for local development and tests.

Use SQLAlchemy or an equivalent mature ORM.

Use Alembic or an equivalent migration system.

### Acceptance criteria

- models exist with tests
- migrations create the complete initial schema
- raw records are immutable through the application service
- schema versions exist
- existing site and asset concepts are migrated or adapted
- one test incident can be stored and reloaded

---

# 7. Phase 3 — Generic File-Based Ingestion

## Goal

Allow a diagnostic to begin without live customer connectivity.

This phase is commercially critical.

## 7.1 First supported formats

Implement:

1. CSV
2. JSON
3. JSONL
4. plain-text structured logs
5. maintenance-ticket CSV/JSON
6. ROS log export
7. rosbag-to-neutral-event export

Do not build ten vendor-specific connectors.

## 7.2 Ingestion workflow

```text
Create diagnostic engagement
→ Register data source
→ Upload file
→ Hash and preserve file
→ Detect format
→ Preview records
→ Apply mapping
→ Validate
→ Ingest raw records
→ Normalize canonical events
→ Produce ingestion summary
```

## 7.3 Mapping configuration

Create reusable YAML or JSON mapping profiles.

Example:

```yaml
mapping_version: "1.0"
name: "generic_robot_error_csv"
source_type: "robot_log"
file:
  format: "csv"
  delimiter: ","
timestamp:
  field: "event_time"
  format: "iso8601"
  timezone: "Europe/Berlin"
identity:
  source_record_id: "record_id"
asset_mapping:
  external_asset_id_field: "robot_id"
fields:
  event_type:
    constant: "robot.error"
  event_code:
    from: "error_code"
  severity:
    from: "severity"
  message:
    from: "message"
  state_from:
    from: "previous_state"
  state_to:
    from: "current_state"
attributes:
  battery_percent:
    from: "battery"
  map_id:
    from: "map"
```

## 7.4 Preview before import

The user must see:

- detected columns
- timestamp interpretation
- sample records
- proposed asset mappings
- validation errors
- records that will be skipped
- unknown event codes

No permanent import should happen until the user confirms or the API request explicitly commits the import.

## 7.5 File preservation

Store:

- original filename
- MIME type
- size
- SHA-256
- upload time
- uploader
- diagnostic engagement
- source type
- storage path
- original unmodified bytes

## 7.6 Import summary

Generate:

```json
{
  "records_seen": 1000,
  "raw_records_created": 998,
  "events_normalized": 950,
  "records_skipped": 2,
  "unknown_assets": 8,
  "unknown_event_codes": 14,
  "timestamp_errors": 4,
  "duplicates": 30
}
```

### Acceptance criteria

- a user can create an engagement and upload three source files
- all original records are preserved
- mapping preview works
- import errors are visible
- normalized events contain provenance
- duplicate import is idempotent
- malformed fixture files fail safely

---

# 8. Phase 4 — Site, System, Asset and Dependency Registry

## Goal

Extend the current asset registry into a mixed-system operational model.

## 8.1 Required hierarchy

```text
Customer
└── Site
    ├── Area
    ├── System
    └── Asset
```

## 8.2 Example systems

- AMR fleet
- WMS
- WES
- WCS
- PLC network
- conveyor system
- automated door system
- lift system
- charging system
- Wi-Fi/network system
- safety system
- maintenance system

## 8.3 Asset metadata

Required:

- name
- external IDs
- asset type
- vendor
- product/model
- software version
- firmware version
- criticality
- operational owner
- maintenance owner
- location
- parent system
- commissioning date if known
- active period
- source aliases

## 8.4 Dependencies

Support directed dependencies:

```text
AMR-07 depends_on WiFi-Zone-A
AMR-07 interacts_with Door-04
Door-04 controlled_by PLC-02
AMR-07 receives_tasks_from FleetManager-01
FleetManager-01 receives_orders_from WCS-01
Charger-02 supplies AMR-Fleet-A
```

Dependency types:

- depends_on
- controlled_by
- communicates_with
- supplies
- receives_tasks_from
- located_in
- blocks
- triggers
- monitored_by
- maintained_by

## 8.5 Asset matching

Implement matching by:

- exact external ID
- alias
- hostname
- IP address
- MAC address
- serial number
- robot name
- configured mapping rule
- analyst confirmation

Never silently assign an ambiguous asset.

### Acceptance criteria

- current YAML asset registry can be imported
- external IDs can map events to assets
- ambiguous mappings create review items
- dependencies are visible in API and UI
- timeline can filter by system and asset

---

# 9. Phase 5 — Timeline Reconstruction Engine

## Goal

Create the first truly differentiated product capability.

## 9.1 Timeline inputs

- canonical events
- raw records
- maintenance tickets
- operator notes
- screenshots and evidence
- manual timeline annotations

## 9.2 Timeline features

Implement:

- chronological ordering
- source filtering
- system filtering
- asset filtering
- severity filtering
- event-type filtering
- event grouping
- duplicate collapse
- related-event linking
- manual annotations
- incident boundary markers
- downtime markers
- recovery markers
- confidence and time-quality display

## 9.3 Timestamp handling

Support:

- UTC
- explicit offsets
- configured source time zones
- naive timestamps
- epoch seconds
- epoch milliseconds
- custom patterns
- known clock offsets
- analyst-adjusted offsets
- uncertainty windows

Store:

```text
original timestamp
parsed timestamp
normalized UTC timestamp
clock offset applied
time quality
parser version
```

## 9.4 Clock alignment

Initial implementation may be analyst-assisted.

Allow the analyst to define:

```text
Source A clock = Source B clock + 3.4 seconds
```

Later methods may estimate alignment using shared events.

Do not claim automatic clock synchronisation unless implemented and tested.

## 9.5 Incident window selection

Allow:

- manual start/end
- expansion before and after the suspected failure
- event-based boundary suggestions
- multiple downtime segments
- excluded planned stops

## 9.6 Timeline API

Recommended endpoints:

```text
GET  /incidents/{id}/timeline
POST /incidents/{id}/timeline/annotations
POST /incidents/{id}/timeline/clock-offsets
POST /incidents/{id}/timeline/boundaries
GET  /incidents/{id}/timeline/export
```

### Acceptance criteria

- at least three independent sources appear in one timeline
- source provenance is visible for every entry
- clock offsets can be reviewed and changed
- changing an offset updates ordering reproducibly
- filters work
- analyst annotations persist
- timeline export is deterministic

---

# 10. Phase 6 — Incident, Downtime and Recovery Model

## Goal

Convert a collection of events into an operational incident.

## 10.1 Incident workflow

```text
Draft
→ Open
→ Investigating
→ Review
→ Resolved
→ Closed
```

## 10.2 Incident creation

Support:

- manual creation
- creation from selected timeline events
- creation from a suggested event cluster
- linking several source events
- attaching affected systems and assets

## 10.3 Downtime model

Do not store only one number.

Implement:

```text
DowntimeSegment
- started_at
- ended_at
- duration_seconds
- type:
    complete_stop
    degraded_operation
    blocked_robot
    manual_intervention
    waiting_for_vendor
    planned
    excluded
- affected_asset_ids
- business_impact
- evidence_links
- analyst_approved
```

Calculate:

- gross incident duration
- unplanned downtime
- degraded-operation duration
- time to detection
- time to acknowledgement
- time to initial diagnosis
- time to recovery
- time to closure

## 10.4 Recovery actions

Track:

- reset
- restart
- mission retry
- manual move
- component replacement
- network intervention
- software rollback
- configuration change
- vendor intervention
- unknown/manual note

For every action:

- who performed it
- when
- affected asset
- source
- outcome
- supporting evidence

### Acceptance criteria

- one incident contains multiple downtime segments
- planned pauses can be excluded
- metrics recalculate after analyst edits
- recovery actions appear in the timeline
- all calculated values retain derivation metadata

---

# 11. Phase 7 — Root-Cause Hypothesis and Evidence System

## Goal

Support disciplined investigation without pretending to provide certain automated causality.

## 11.1 Hypothesis model

Each hypothesis must include:

- title
- failure domain
- description
- status
- confidence
- supporting evidence
- contradicting evidence
- missing expected evidence
- assumptions
- analyst owner
- approval status

Failure domains:

- robot hardware
- robot software
- localisation/navigation
- fleet manager
- WMS/WCS/WES
- PLC/control
- door/lift/conveyor
- charging
- network/Wi-Fi
- safety system
- human operation
- maintenance
- configuration
- integration/interface
- unknown

## 11.2 Hypothesis states

```text
proposed
under_review
supported
rejected
inconclusive
confirmed
```

Only a human analyst can mark a hypothesis as confirmed.

## 11.3 Confidence

Initial confidence may be analyst-entered.

If rule-based scoring is implemented, make the calculation visible.

Example:

```text
Base score: 0.30
Two supporting events: +0.25
One contradicting event: -0.15
Missing WCS logs: confidence capped at 0.65
Final score: 0.40
```

Do not use unexplained AI confidence.

## 11.4 AI assistance

AI may later:

- summarize evidence
- suggest candidate hypotheses
- classify event descriptions
- propose missing sources
- draft report wording

AI must not:

- silently change evidence
- mark a cause confirmed
- hide contradictions
- produce unsupported conclusions
- replace human approval

Every AI-generated artifact must include:

- model/provider if applicable
- prompt/version identifier
- generation timestamp
- source evidence IDs
- reviewer status

### Acceptance criteria

- hypotheses can be created manually
- evidence can support or contradict
- missing evidence is explicit
- confidence calculation is inspectable
- confirmed status requires human action
- report shows alternatives, not only one conclusion

---

# 12. Phase 8 — Data-Quality Assessment

## Goal

Make uncertainty a product feature rather than hiding it.

## 12.1 Required checks

Implement:

- missing source
- missing interval
- duplicate record
- timestamp parse failure
- time-zone uncertainty
- clock-offset uncertainty
- impossible ordering
- unsupported event code
- unmatched asset
- stale data
- corrupted file
- truncated export
- inconsistent units
- conflicting state transitions
- unexplained data gap

## 12.2 Data-quality summary

Per incident, calculate:

```text
source completeness
timestamp confidence
asset-mapping confidence
event-normalisation coverage
unknown-event percentage
missing critical sources
overall evidence sufficiency
```

Use descriptive categories initially:

```text
high
medium
low
insufficient
```

## 12.3 Confidence caps

Examples:

- if no fleet-manager data exists, fleet-manager conclusions cannot be confirmed
- if clocks are unsynchronised, event order must show uncertainty
- if only screenshots exist, exact timing cannot be claimed
- if WCS logs are missing, ownership conclusions remain limited

### Acceptance criteria

- every diagnostic report includes a data-quality section
- missing sources are visible
- uncertainty affects hypothesis confidence
- no report can claim complete evidence when critical sources are absent

---

# 13. Phase 9 — Convert FleetWatch into Incident Console

## Goal

Reuse the current operator layer as the main investigation UI.

## 13.1 Main navigation

Replace the startup-facing UI structure with:

```text
Overview
Diagnostic engagements
Incidents
Timeline
Evidence
Assets and systems
Data sources
Data quality
Hypotheses
Corrective actions
Support cases
Reports
Administration
```

## 13.2 Dashboard

Display:

- open incidents
- incidents awaiting review
- average diagnostic duration
- downtime by system
- recurring incident patterns
- missing-source warnings
- unresolved high-severity findings
- support cases awaiting response

Do not make generic robot telemetry charts the main dashboard.

## 13.3 Diagnostic engagement screen

Required:

- customer/site
- engagement status
- uploaded sources
- ingestion status
- incident list
- analyst
- commercial reference
- report status
- delivery date
- validation outcome

## 13.4 Incident screen

Required tabs:

```text
Summary
Timeline
Evidence
Hypotheses
Downtime
Recovery
Data quality
Actions
Support case
Reports
Audit history
```

## 13.5 Evidence viewer

Support:

- raw log record
- source file context
- image
- screenshot
- PDF reference
- ticket
- analyst note
- generated chart
- report excerpt

## 13.6 Human review

Every automated or generated conclusion must be editable and approvable.

### Acceptance criteria

- one complete historical diagnostic can be performed through UI
- analyst does not need database access
- raw evidence is reachable from timeline entries
- incident status and assignments work
- audit history records important actions

---

# 14. Phase 10 — Diagnostic Report and Vendor-Support Package

## Goal

Turn the analysis into the first sellable deliverable.

## 14.1 Required report sections

Generate:

```text
1. Executive summary
2. Incident scope
3. Operational impact
4. Systems and assets involved
5. Source inventory
6. Reconstructed timeline
7. Downtime and recovery metrics
8. Most likely cause
9. Alternative hypotheses
10. Supporting evidence
11. Contradicting evidence
12. Missing evidence
13. Data-quality limitations
14. Corrective actions
15. Recurrence risk
16. Vendor-support recommendations
17. Appendix
18. Audit and provenance
```

## 14.2 Formats

Generate:

- JSON
- Markdown
- HTML
- CSV timeline export
- PDF if an existing approved PDF generation path is available later
- ZIP vendor-support package

## 14.3 Vendor-support package

Include only selected relevant evidence:

```text
incident_summary.md
timeline.csv
affected_assets.json
selected_raw_logs/
screenshots/
evidence_manifest.json
questions_for_vendor.md
data_quality_notes.md
```

The package must not automatically include unrelated logs or personal worker data.

## 14.4 Evidence manifest

Every package must include:

- file name
- SHA-256
- source
- original timestamp
- export timestamp
- included-by
- reason for inclusion

### Acceptance criteria

- report is generated from stored structured data
- every important conclusion links to evidence
- report identifies missing evidence
- vendor package is reproducible
- report can be regenerated without changing previous approved versions
- final report requires analyst approval

---

# 15. Phase 11 — Synthetic Cross-System Incident Lab

## Goal

Use the existing ROS/Gazebo project as a controlled incident-data generator.

## 15.1 Preserve autonomy demo

Move the existing robot project under:

```text
autonomy_demo/
```

or keep it as a separately launched workspace referenced by the startup repository.

## 15.2 Create synthetic exporters

Generate independent source files as though they came from:

- robot controller
- fleet manager
- WCS
- door PLC
- Wi-Fi controller
- charger
- maintenance ticket system

Each source must:

- have its own schema
- use different identifiers
- optionally use a different clock offset
- contain irrelevant events
- contain missing data in some scenarios
- avoid sharing hidden ground-truth labels with the incident engine

## 15.3 Required benchmark scenarios

### Scenario 1 — Door and Wi-Fi ambiguity

```text
Robot approaches door
Wi-Fi roaming event occurs
Fleet command is delayed
Door release arrives late
Robot reports blocked path
Operator retries
Mission resumes
```

The engine should reconstruct the sequence and avoid claiming certainty if WCS data is missing.

### Scenario 2 — Charger failure

```text
Robot reports charging
Battery percentage does not increase
Charger PLC reports intermittent contact
Fleet manager repeatedly dispatches robot
Maintenance cleans connector
Charging recovers
```

### Scenario 3 — WCS integration delay

```text
Robot is healthy
Fleet manager waits for task confirmation
WCS event delivery is delayed
Robot remains idle
Operator restarts integration service
Tasks resume
```

### Scenario 4 — Localisation symptoms caused by network loss

```text
Robot reports navigation recovery
Map service response times increase
Wi-Fi signal drops
No robot hardware error exists
Network returns
Navigation resumes
```

## 15.4 Ground truth

Ground truth may exist only for test assertions.

The application must not read the ground-truth file during analysis.

### Acceptance criteria

- three complete fixtures exist
- each includes at least three source types
- each includes irrelevant noise
- at least one includes missing evidence
- at least one includes clock drift
- end-to-end analysis produces a usable report
- ground truth is used only by tests

---

# 16. Phase 12 — API Requirements

## Goal

Create a stable product API.

## 16.1 Recommended API groups

```text
/auth
/users
/roles
/customers
/sites
/systems
/assets
/dependencies
/data-sources
/ingestion-runs
/raw-records
/events
/diagnostic-engagements
/incidents
/timelines
/downtime
/recovery-actions
/hypotheses
/evidence
/data-quality
/corrective-actions
/support-cases
/reports
/audit
```

## 16.2 Important endpoints

```text
POST /diagnostic-engagements
POST /diagnostic-engagements/{id}/sources
POST /sources/{id}/uploads
POST /ingestion-runs/{id}/preview
POST /ingestion-runs/{id}/commit
GET  /ingestion-runs/{id}/summary

POST /incidents
GET  /incidents/{id}
PATCH /incidents/{id}
GET  /incidents/{id}/timeline
POST /incidents/{id}/events
POST /incidents/{id}/clock-offsets
POST /incidents/{id}/downtime-segments

POST /incidents/{id}/hypotheses
POST /hypotheses/{id}/evidence
PATCH /hypotheses/{id}/status

GET  /incidents/{id}/data-quality
POST /incidents/{id}/data-quality/recalculate

POST /incidents/{id}/reports
GET  /reports/{id}
POST /reports/{id}/approve
POST /incidents/{id}/vendor-package
```

## 16.3 API behavior

- use pagination
- validate all input
- return structured errors
- use idempotency keys for ingestion
- never expose local file paths
- enforce permissions
- include schema versions
- provide OpenAPI documentation
- log important write operations

### Acceptance criteria

- contract tests exist
- OpenAPI is generated
- permissions are tested
- duplicate ingestion is safe
- invalid input fails clearly

---

# 17. Phase 13 — Security and Industrial Procurement Baseline

## Goal

Reach a credible pilot-ready security baseline.

This is not full certification.

## 17.1 Authentication

Implement:

- secure password hashing
- session or token expiry
- account disablement
- password reset workflow
- optional future OIDC support

## 17.2 Roles

Minimum roles:

```text
admin
analyst
reviewer
operator
partner
viewer
```

## 17.3 Permission examples

- viewer cannot upload or modify
- analyst can create and investigate
- reviewer can approve reports
- partner sees only assigned customer environments
- admin manages users and retention

## 17.4 Audit log

Record:

- login
- upload
- ingestion commit
- mapping change
- asset mapping
- clock-offset change
- incident boundary change
- hypothesis change
- report generation
- report approval
- export
- deletion
- permission change

Audit events must be append-only through the application.

## 17.5 Secrets

Use environment variables or a secrets manager.

Never commit:

- passwords
- API keys
- certificates
- customer credentials
- database passwords

Provide:

```text
.env.example
```

## 17.6 Encryption

Target:

- HTTPS/TLS
- encrypted database volume where practical
- encrypted file storage where practical
- secure backups

## 17.7 Data minimisation

Worker-related data must be:

- avoided by default
- redacted where possible
- separately permissioned
- excluded from support exports unless required
- documented in retention policies

## 17.8 Vulnerability process

Create:

```text
SECURITY.md
docs/security/vulnerability_management.md
docs/security/update_policy.md
docs/security/data_retention.md
docs/security/incident_response.md
```

### Acceptance criteria

- RBAC tests pass
- audit events exist
- no secrets are committed
- upload validation exists
- file-size limits exist
- dangerous file types are rejected or isolated
- documented vulnerability-reporting process exists

---

# 18. Phase 14 — Deployment

## Goal

Support a real pilot without requiring a complex cloud platform.

## 18.1 Initial deployment modes

Support:

### Local diagnostic workstation

```text
Docker Compose
PostgreSQL
API
UI
worker
local evidence storage
```

### On-prem pilot

```text
single customer
outbound-only optional
no inbound internet requirement
customer-controlled storage
```

Do not build multi-region SaaS infrastructure initially.

## 18.2 Docker Compose services

Recommended:

```yaml
services:
  db:
  api:
  ui:
  worker:
  object_store:
```

MinIO may be used for local S3-compatible evidence storage.

## 18.3 Health checks

Provide:

- database health
- API health
- worker health
- storage health
- migration status

## 18.4 Backups

Document:

- database backup
- evidence backup
- restore procedure
- verification procedure

### Acceptance criteria

- one command starts the system
- clean machine setup is documented
- migrations run safely
- fixture diagnostic can be loaded
- backup and restore are tested

---

# 19. Phase 15 — Testing Strategy

## 19.1 Unit tests

Test:

- timestamp parsing
- mapping rules
- event normalisation
- duplicate detection
- downtime calculation
- confidence rules
- data-quality checks
- permission checks

## 19.2 Contract tests

Test:

- connector output schema
- API schemas
- report schemas
- migration compatibility
- evidence manifest

## 19.3 Integration tests

Test:

- upload to raw records
- raw records to events
- events to timeline
- timeline to incident
- incident to report
- report to vendor package

## 19.4 Security tests

Test:

- unauthorised access
- cross-customer access
- path traversal
- oversized upload
- invalid MIME type
- malicious CSV formula
- SQL injection
- unsafe file names
- role escalation

## 19.5 Regression tests

Preserve:

- current asset import
- current evidence model where reused
- current report output where adapted
- benchmark synthetic data generation

## 19.6 End-to-end tests

For each fixture:

```text
create engagement
upload files
preview mappings
commit ingestion
map assets
create incident
define timeline
create hypothesis
link evidence
calculate downtime
approve report
export support package
```

### Acceptance criteria

- all critical flows are automated
- CI runs unit and integration tests
- end-to-end fixture test passes
- no production claim is based only on unit tests

---

# 20. Phase 16 — Validation Board Integration

## Goal

Make commercial learning part of the product workflow.

## 20.1 Required validation records

Track:

```text
Operator interview
Integrator interview
Dataset request
Dataset received
Diagnostic performed
Actionable outcome
Proposal sent
Proposal accepted
Pilot started
Security review
Partner introduction
Commercial commitment
Confidence update
```

## 20.2 Required hypothesis gates

### Problem gate

Pass when:

```text
8 of 15 operators independently confirm repeated and costly diagnosis problems
```

### Access gate

Pass when:

```text
three usable sites or datasets
and at least two source types per relevant incident
```

### Value gate

Pass when:

```text
two of three diagnostics produce an actionable result
```

### Payment gate

Pass when:

```text
two paid diagnostics
or one paid pilot
```

### Partner gate

Pass when:

```text
two customer introductions
and one commercial commitment
```

### Reusability gate

Pass when:

```text
at least 70% of ingestion, analysis and reporting components are reused in the second deployment
```

### Security gate

Pass when:

```text
one real customer or integrator accepts the deployment architecture
```

### Market gate

Pass when:

```text
at least 100 named high-fit accounts exist
```

### Pricing gate

Pass when:

```text
two buyers accept €15,000+ annual production pricing
```

## 20.3 Do not fake completion

A synthetic dataset does not pass:

- access gate
- value gate
- payment gate
- partner gate
- security gate
- pricing gate

### Acceptance criteria

- validation records exist in the repository or connected board
- confidence changes are documented
- every go/pivot/stop decision links to evidence

---

# 21. Exact Build Order

Codex must follow this order unless blocked by a documented dependency.

## Milestone 1 — Working product shell

1. copy and baseline repo
2. create new product docs
3. create target folder structure
4. separate autonomy demo
5. create PostgreSQL and migrations
6. implement core entities
7. migrate current site and asset model
8. expose basic CRUD API
9. update README
10. add baseline tests

**Deliverable:** the copied repository runs as an incident-intelligence application shell while the old demo remains available.

---

## Milestone 2 — Historical data ingestion

1. upload storage
2. file hashing
3. data-source registry
4. CSV preview
5. JSON preview
6. mapping configuration
7. raw-record persistence
8. canonical-event normalisation
9. ingestion summary
10. malformed-file tests

**Deliverable:** three external files can be ingested without ROS.

---

## Milestone 3 — Timeline and incident workflow

1. event browser
2. event filters
3. asset mapping
4. clock offsets
5. incident creation
6. timeline view
7. downtime segments
8. recovery actions
9. analyst annotations
10. audit log

**Deliverable:** an analyst can reconstruct a multi-source incident.

---

## Milestone 4 — Evidence and hypotheses

1. hypothesis model
2. evidence relations
3. contradicting evidence
4. missing evidence
5. confidence calculation
6. data-quality checks
7. human approval
8. incident review page

**Deliverable:** conclusions are traceable and uncertainty is explicit.

---

## Milestone 5 — Sellable diagnostic report

1. report model
2. report templates
3. timeline export
4. evidence appendix
5. vendor question generator
6. evidence manifest
7. report approval
8. ZIP vendor package
9. immutable approved report version
10. sample diagnostic

**Deliverable:** one complete €1,000–€3,000-style historical diagnostic package.

---

## Milestone 6 — Synthetic incident lab

1. reorganise ROS demo
2. create source exporters
3. build door/Wi-Fi scenario
4. build charger scenario
5. build WCS delay scenario
6. add clock drift
7. add irrelevant events
8. add missing data
9. end-to-end tests
10. demo documentation

**Deliverable:** reproducible multi-system incident demonstrations.

---

## Milestone 7 — Pilot readiness

1. RBAC
2. secure upload
3. secrets management
4. security docs
5. Docker Compose
6. backup and restore
7. on-prem deployment guide
8. data retention
9. customer import checklist
10. diagnostic delivery checklist

**Deliverable:** credible architecture for one real paid or unpaid pilot.

---

# 22. Initial UI Wireframe

## 22.1 Overview

```text
---------------------------------------------------------
Open incidents: 4
Awaiting review: 2
Missing critical sources: 3
Total downtime under review: 11 h 24 min
---------------------------------------------------------
Recent incidents
- AMR blocked at Door 04
- Charger 02 intermittent contact
- WCS task delay affecting Fleet A
---------------------------------------------------------
```

## 22.2 Incident timeline

```text
09:13:02  Wi-Fi     AP roaming started
09:13:05  Robot     Navigation recovery activated
09:13:08  Fleet     Mission paused
09:13:11  Door PLC  Door release request received
09:13:17  Door PLC  Door open confirmed
09:13:21  Robot     Path resumed
```

Each row must show:

- source
- asset/system
- timestamp quality
- raw evidence link
- severity
- evidence status
- analyst annotation

## 22.3 Hypothesis panel

```text
Hypothesis A: Wi-Fi interruption delayed command delivery
Confidence: Medium, 0.62

Supporting:
- AP roaming event
- robot recovery event
- delayed fleet acknowledgement

Contradicting:
- door PLC received request normally

Missing:
- WCS network trace
```

---

# 23. Initial Connector SDK

## Goal

Make future integrations reusable without building them now.

## 23.1 Connector interface

Every connector should implement:

```python
class Connector:
    def validate_configuration(self) -> ValidationResult:
        ...

    def preview(self) -> PreviewResult:
        ...

    def ingest(self) -> IngestionResult:
        ...

    def normalize(self, raw_record: RawRecord) -> list[CanonicalEvent]:
        ...

    def health(self) -> ConnectorHealth:
        ...
```

## 23.2 Connector metadata

- connector name
- version
- source type
- supported formats
- authentication requirements
- read-only declaration
- required permissions
- schema version
- vendor status
- maturity level:
  - experimental
  - validated
  - production candidate
  - production

## 23.3 Connector rules

- connectors cannot write to customer systems
- connector permissions must be documented
- connectors must emit provenance
- failures must not lose raw data
- unknown fields must be preserved
- connector-specific logic must not enter the incident core

---

# 24. What Not to Build Yet

Do not implement these before the historical diagnostic is used on real data:

- predictive maintenance models
- fleet optimisation
- mission allocation
- traffic control
- digital twin
- 3D warehouse visualisation
- generic live telemetry wallboard
- multi-cloud deployment
- Kubernetes
- ten vendor connectors
- autonomous root-cause confirmation
- cross-customer benchmarking
- public connector marketplace
- mobile application
- advanced billing
- large language model chat interface
- VDA 5050 control bridge
- robot teleoperation
- full CMMS replacement
- worker-performance analytics

---

# 25. Definition of 100/100 for the Validation-Ready MVP

The MVP reaches 100/100 only when all conditions below are true.

## Product

- [ ] product is clearly incident intelligence, not robot control
- [ ] workflow starts from external historical files
- [ ] product works without ROS
- [ ] raw evidence is preserved
- [ ] events are normalised
- [ ] assets and systems are linked
- [ ] multi-source timeline exists
- [ ] timestamps and clock offsets are reviewable
- [ ] incidents have boundaries
- [ ] downtime is calculated
- [ ] recovery actions are tracked
- [ ] hypotheses contain evidence
- [ ] contradictions are visible
- [ ] missing evidence is visible
- [ ] data quality is scored
- [ ] analyst approval exists
- [ ] report is generated
- [ ] vendor package is exported

## Engineering

- [ ] PostgreSQL migrations work
- [ ] Docker Compose works
- [ ] tests pass
- [ ] RBAC works
- [ ] audit log works
- [ ] uploads are secure
- [ ] secrets are not committed
- [ ] backups and restore are tested
- [ ] API documentation exists
- [ ] schemas are versioned
- [ ] duplicate imports are idempotent
- [ ] approved reports are versioned and immutable

## Demonstration

- [ ] three synthetic cross-system incidents exist
- [ ] each uses at least three source types
- [ ] one includes missing data
- [ ] one includes clock drift
- [ ] one includes contradicting evidence
- [ ] end-to-end report is generated

## Commercial validation

The software can be called **validation-ready** without real customers.

It cannot be called **validated** until:

- [ ] at least one real operator dataset is analysed
- [ ] the result is reviewed by the operator
- [ ] the result changes or supports a real decision
- [ ] one buyer discusses a paid diagnostic
- [ ] customer data-access and security objections are recorded

---

# 26. First Real Customer Workflow

When a customer or friendly operator agrees:

## Step 1 — Scope

Collect:

- site
- affected process
- incident date and time
- affected robots/assets
- operational impact
- known systems
- known support tickets
- available source files

## Step 2 — Data request

Request only relevant data:

- 30–60 minutes before incident
- incident interval
- 30–60 minutes after recovery

## Step 3 — Ingestion

- create engagement
- register sources
- upload
- hash
- preview
- map
- ingest
- review errors

## Step 4 — Analysis

- align clocks
- define incident boundaries
- identify affected assets
- mark downtime
- record recovery actions
- create hypotheses
- link evidence
- identify missing sources

## Step 5 — Review

Review with:

- maintenance
- operations
- automation/controls
- robot integrator if applicable

## Step 6 — Deliver

Provide:

- report
- timeline
- evidence package
- corrective actions
- open questions
- recommended monitoring changes

## Step 7 — Record outcome

Record:

- was the conclusion accepted?
- did it change a decision?
- did it reduce support time?
- did the customer request live deployment?
- did they pay?
- what was reusable?
- what required custom work?

---

# 27. Metrics to Track

## Product metrics

- time to import first dataset
- percentage of records normalised
- percentage of records mapped to assets
- percentage of unknown event codes
- time to construct timeline
- time to produce report
- number of manual corrections
- number of missing critical sources
- percentage of report statements linked to evidence

## Value metrics

- hours saved in diagnosis
- downtime clarified
- support-case preparation time saved
- number of previously unknown contributing factors
- number of recurring incidents identified
- number of corrective actions accepted
- customer willingness to pay
- annual production pricing accepted

## Reusability metrics

- percentage of reused connector code
- percentage of reused mapping rules
- percentage of reused report logic
- customer-specific engineering hours
- deployment time
- number of manual data transformations

---

# 28. Go, Pivot and Stop Conditions

## GO

Continue toward live pilots when:

- at least one real diagnostic is completed
- evidence is usable
- an operator confirms value
- software reuse is high
- customer security objections are manageable
- payment discussions are positive

## PIVOT

Pivot the product or customer segment when:

- logs exist but cross-system correlation is not considered valuable
- integrators want an internal toolkit rather than direct SaaS
- customers mainly pay for reporting or SLA evidence
- network correlation is consistently the highest-value use case
- live data is unavailable but recurring historical diagnostics sell

Possible pivots:

- integrator white-label diagnostic toolkit
- vendor-support evidence platform
- robot plus Wi-Fi incident analytics
- SLA/warranty reporting
- managed reliability diagnostics

## STOP

Stop or fundamentally rethink when:

- fewer than 8 of 15 operators confirm the problem
- no usable data is obtained from three serious attempts
- diagnostics do not change decisions
- nobody pays for diagnostics or pilots
- deployment requires excessive custom engineering
- integrators consistently rebuild the functionality
- reachable high-fit market remains below 100 named accounts
- customer security requirements make the architecture infeasible

---

# 29. Codex Working Rules

Codex must:

1. make small, reviewable commits
2. update this file with completed checkboxes
3. create a phase report after every milestone
4. run tests before marking a task complete
5. document assumptions
6. use synthetic fixtures when real data is unavailable
7. clearly label simulated outputs
8. preserve raw data and provenance
9. maintain backwards compatibility until migration is complete
10. avoid adding unnecessary infrastructure
11. avoid unreviewed AI decision-making
12. never invent validation results
13. never claim customer support that has not been verified
14. stop and document blockers rather than silently bypassing controls
15. keep the historical diagnostic as the first complete product workflow

---

# 30. Immediate First Sprint

This is the exact first sprint Codex should execute.

## Sprint objective

Create the incident-intelligence product shell while preserving the existing demo.

## Tasks

### Task 1

Create the new folder structure.

### Task 2

Move or reference the current ROS project under `autonomy_demo/`.

Do not break its build.

### Task 3

Create the four product-definition documents.

### Task 4

Update the root README with:

- startup product
- first diagnostic offer
- architecture overview
- current status
- simulated versus real
- quick-start instructions

### Task 5

Create PostgreSQL Docker Compose service.

### Task 6

Create migrations for:

- Customer
- Site
- System
- Asset
- DataSource
- DiagnosticEngagement
- IngestionRun
- RawRecord
- CanonicalEvent
- Incident
- TimelineEntry
- DataQualityIssue

### Task 7

Create a generic CSV ingestion preview endpoint.

### Task 8

Create a sample CSV fixture containing:

- robot events
- at least one invalid timestamp
- one duplicate
- one unknown asset
- one unknown event code

### Task 9

Create ingestion summary output.

### Task 10

Create tests for:

- file hashing
- preview
- duplicate detection
- timestamp parsing
- raw-record immutability

## First sprint acceptance criteria

- startup application starts without ROS
- PostgreSQL starts
- migrations run
- sample CSV can be previewed
- sample CSV can be ingested
- raw records are stored
- canonical events are created
- errors are reported
- tests pass
- ROS demo still builds separately
- phase report is created

---

# 31. Second Sprint

## Sprint objective

Create the first multi-source incident timeline.

## Tasks

1. add generic JSON importer
2. add maintenance-ticket importer
3. implement system and asset aliases
4. implement asset mapping review
5. create incident CRUD
6. build timeline endpoint
7. build timeline UI
8. add clock-offset configuration
9. add analyst annotations
10. create three-source fixture

## Acceptance criteria

- CSV, JSON and ticket data appear in one timeline
- every event links to raw evidence
- analyst can change clock offset
- analyst can create incident boundaries
- source and asset filters work

---

# 32. Third Sprint

## Sprint objective

Create the first sellable diagnostic output.

## Tasks

1. implement downtime segments
2. implement recovery actions
3. implement hypotheses
4. implement evidence relations
5. implement data-quality summary
6. create report template
7. generate HTML and JSON report
8. generate vendor-support ZIP
9. add approval workflow
10. complete end-to-end fixture test

## Acceptance criteria

- one incident has a complete report
- conclusions link to evidence
- contradictions are visible
- missing sources are visible
- vendor package is generated
- approved report is versioned

---

# 33. Final Product Statement

Use this wording as the working product definition:

> Robot Fleet Incident Intelligence is a read-only incident and reliability layer for brownfield warehouses and factories. It combines evidence from robots, fleet software, WMS/WCS, PLCs, chargers, doors, lifts, network systems and maintenance records; normalises those records; reconstructs stoppages; measures downtime and recovery; evaluates evidence quality; and produces traceable maintenance and vendor-support reports. The business begins with paid historical incident diagnostics and later becomes an on-premise or EU-hosted production platform distributed directly and through independent integrators.

---

# 34. Final Implementation Priority

The priority order is:

```text
1. Historical file ingestion
2. Raw evidence and provenance
3. Canonical event model
4. Asset and system mapping
5. Multi-source timeline
6. Incident boundaries
7. Downtime and recovery
8. Evidence and hypotheses
9. Data quality
10. Diagnostic report
11. Vendor-support package
12. Security and on-prem deployment
13. Real customer diagnostic
14. Integrator workflow
15. Live connectors
16. AI assistance
```

Do not change this order without documenting why.

---

# 35. Final Instruction to Codex

The copied repository must not become a larger robotics demo.

It must become the smallest credible system capable of performing a real historical warehouse-robot incident diagnostic.

The first success condition is not:

```text
The robot navigates better.
```

The first success condition is:

```text
A real operator gives us several imperfect data exports, and the product helps reconstruct what happened, how long the disruption lasted, what evidence supports the conclusion, what remains unknown and what the operator should do next.
```
