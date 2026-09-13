# ADVANCE.md

# Factory Inspection Startup Product Advancement Specification

## Purpose

This document is the implementation roadmap for advancing the current ROS 2 + Nav2 autonomous factory inspection project from a strong simulation prototype into a startup-grade industrial inspection product architecture.

It is written for Codex or another coding agent that will inspect the repository, plan changes, implement features incrementally, run tests, and preserve working behavior.

The current system already provides:

- Gazebo-based warehouse/factory simulation
- ROS 2 launch architecture
- Nav2 waypoint patrol
- Checkpoint inspection hooks
- Evidence image storage
- Structured anomaly outputs
- Mission-level decisions
- JSON, CSV, Markdown, and HTML reports
- Multi-round campaign behavior
- Modular separation between navigation, mission, inspection, and reporting

The goal is **not** to discard this architecture. The goal is to evolve it into a robust, asset-centered, measurable, secure, extensible, operator-usable industrial inspection platform.

---

# 1. Product Goal

The target product is:

> A hardware-extensible autonomous inspection platform that schedules asset inspections, directs one or more robots to inspection points, collects multimodal evidence, evaluates asset condition, manages findings through an operator workflow, tracks asset history, integrates with industrial systems, and provides traceable, measurable, secure inspection operations.

The platform must eventually support:

- One or more mobile robots
- Multiple inspection skills
- Multiple sites
- Asset-centered mission planning
- Repeatable inspection viewpoints
- Findings and maintenance workflows
- Historical trend analysis
- Simulation and physical deployment
- Secure edge deployment
- External integrations
- Automated regression testing
- Model and rule traceability
- Operational observability
- Human confirmation and feedback
- Future real industrial data

---

# 2. Important Product Reality

A “100/100 startup product” cannot be achieved through code alone.

The repository can be advanced to a **100/100 engineering-ready product foundation**, but final commercial readiness will still require:

- Real customer discovery
- Real industrial data
- Real robot testing
- Safety review
- Cybersecurity review
- Pilot deployment
- Measured customer value
- Legal and regulatory assessment
- Support and maintenance capability

Because real data is not currently available, Codex must:

1. Build all required interfaces and infrastructure now.
2. Use simulation, fixtures, synthetic datasets, recorded test artifacts, and mocked integrations.
3. Clearly mark future real-data validation gates.
4. Never fabricate production accuracy, reliability, or ROI claims.
5. Keep all real-world claims disabled until supporting evidence exists.

---

# 3. Core Engineering Principles

## 3.1 Preserve working functionality

Do not break:

- Existing launch files
- Existing single-robot benchmark flow
- Existing Nav2 integration
- Existing inspection reports
- Existing evidence capture
- Existing mission decisions

Where replacement is necessary, provide compatibility adapters and migration notes.

## 3.2 Build incrementally

Every major feature must be introduced through:

- A small design document
- A minimal implementation
- Unit tests
- Integration tests
- Launch-level validation
- Documentation
- Clear acceptance criteria

## 3.3 Separate product concepts

Keep these domains distinct:

- Robot navigation
- Mission execution
- Asset model
- Inspection skill
- Evidence storage
- Finding lifecycle
- Operator workflow
- Reporting
- Integrations
- Deployment
- Security
- Analytics

Avoid one oversized node containing all business logic.

## 3.4 Prefer deterministic behavior first

Use deterministic logic before machine learning where possible:

- Rules before learned anomaly classification
- Explicit mission policies before AI-generated mission plans
- Structured findings before natural-language summaries
- Versioned configuration before hidden behavior

## 3.5 Treat AI as an assistant, not the source of truth

Future AI features may:

- Summarize findings
- Suggest likely causes
- Recommend follow-up inspections
- Explain evidence
- Search prior incidents

AI must not:

- Directly control safety-critical equipment
- Override safety systems
- Silently change mission state
- Invent measurements
- Hide underlying evidence
- Claim certainty without supporting data

---

# 4. Current Architecture Baseline

Codex must first inspect the repository and verify the exact implementation.

Expected current components include:

- `benchmark_patrol.launch.py`
- `benchmark_scenario_generator.py`
- `benchmark_world.launch.py`
- `benchmark_robot_instance.launch.py`
- `patrol_mission.launch.py`
- `patrol_mission_node.cpp`
- `inspection_at_waypoint.cpp`
- `mission_report_node.cpp`

Expected conceptual layers:

1. Scenario and simulation
2. Navigation
3. Mission control
4. Checkpoint inspection
5. Reporting

Before modifying code, create:

- `docs/current_architecture.md`
- `docs/current_topic_graph.md`
- `docs/current_launch_flow.md`
- `docs/current_data_outputs.md`
- `docs/current_known_limitations.md`

These files must be based on repository inspection, not assumptions from this document.

---

# 5. Target Product Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        Operator Layer                        │
│ Dashboard | Finding Review | Asset History | Mission Control │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                        Application Layer                     │
│ Asset Registry | Scheduler | Findings | Reports | Analytics  │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                     Inspection Intelligence                 │
│ Skill Registry | Rules | Models | Fusion | Confidence        │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                         Mission Layer                        │
│ Mission Planner | Mission State | Follow-Up | Recovery       │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                       Robot Adapter Layer                    │
│ ROS 2/Nav2 Adapter | Future Vendor Adapters | Health         │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│ Evidence | Events | Findings | Metrics | Audit | Config      │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                     Integration Layer                        │
│ MQTT | REST | OPC UA | WMS/WES | CMMS/EAM | Webhooks        │
└──────────────────────────────────────────────────────────────┘
```

---

# 6. Major Product Gaps

## 6.1 Product definition

- No narrow initial asset category
- No explicit first buyer persona
- No defined inspection service-level objective
- No product-level success metrics
- No formal distinction between simulated and validated capability
- No product feature maturity classification

## 6.2 Asset management

- No persistent asset registry
- No asset hierarchy
- No asset criticality
- No asset owner
- No inspection requirement definition
- No asset-specific thresholds
- No asset inspection frequency
- No persistent point-of-interest model
- No asset-to-checkpoint calibration
- No asset state lifecycle

## 6.3 Inspection

- Inspection results are partly benchmark-driven
- Limited inspection skill abstraction
- No standardized multimodal measurement schema
- No sensor calibration registry
- No model registry
- No rule versioning
- No model performance metadata
- No uncertainty policy
- No robust asset identification
- No evidence quality checks
- No repeatable viewpoint verification
- No inspection preconditions
- No sensor health verification

## 6.4 Mission

- Mission planning is route-centered rather than asset-centered
- Limited scheduling
- Limited interruption and resumption
- Limited recovery
- No mission priority queue
- No inspection due-date logic
- No battery-aware scheduling
- No resource allocation
- No formal mission state machine
- No operator approval flow
- No clear partial-completion behavior
- No robust failure escalation state

## 6.5 Robot abstraction

- Strong coupling to ROS 2/Nav2 assumptions
- No formal robot capability model
- No robot adapter interface
- No tested second robot implementation
- No capability matching
- No robot health abstraction
- No docking abstraction
- No robot-specific mission constraints
- No standardized teleoperation interface

## 6.6 Operator workflow

- No full finding lifecycle
- No assignment
- No acknowledgement
- No comment history
- No false-positive feedback
- No maintenance action record
- No closure verification
- No reinspection request workflow
- No role-based permissions
- No operator notification policy

## 6.7 Historical intelligence

- Limited baseline management
- No degradation trends
- No repeated anomaly grouping
- No recurring finding detection
- No asset health score
- No inspection coverage calculation
- No fleet/site KPI definitions
- No correlation with maintenance actions
- No incident similarity search

## 6.8 Integration

- No stable public API
- No integration SDK
- No MQTT contract
- No OPC UA contract
- No CMMS/EAM connector
- No WMS/WES connector
- No ticketing connector
- No outbound webhook mechanism
- No integration retry and dead-letter handling

## 6.9 Reliability

- No formal long-duration testing
- No fault injection framework
- No recovery matrix
- No watchdog architecture
- No health aggregation
- No corrupted-output recovery
- No disk-full handling
- No network-partition handling
- No process restart persistence
- No deterministic mission replay

## 6.10 Security

- No authentication
- No authorization
- No audit log
- No secret management
- No encrypted external transport policy
- No signed configuration
- No software bill of materials
- No vulnerability scanning
- No update strategy
- No data retention controls
- No tenant/site isolation
- No secure defaults

## 6.11 Deployment

- No documented production edge deployment
- No containerized deployment standard
- No environment profiles
- No configuration validation
- No backup and restore
- No schema migrations
- No update rollback
- No resource usage targets
- No installation diagnostics
- No deployment readiness report

## 6.12 Testing

- Limited unit-test coverage
- Limited launch/integration tests
- No contract tests
- No regression dataset
- No benchmark comparison gate
- No end-to-end scenario matrix
- No mutation or fault testing
- No security tests
- No performance tests
- No evidence integrity tests

## 6.13 Commercial readiness — future gates

These must not block simulation engineering:

- Customer validation
- Willingness to pay
- Pilot agreement
- ROI measurement
- Customer support process
- SLA definition
- Data processing agreement
- Regulatory review
- Liability review
- Insurance
- Procurement readiness
- Sales and onboarding materials

---

# 7. Required Repository Evolution

Codex should propose a target structure similar to the following, adapted to the existing ROS package organization.

```text
factory_inspection/
├── README.md
├── ADVANCE.md
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── config/
│   ├── sites/
│   ├── assets/
│   ├── robots/
│   ├── inspection_skills/
│   ├── mission_policies/
│   └── environments/
├── docs/
│   ├── architecture/
│   ├── operations/
│   ├── security/
│   ├── product/
│   ├── testing/
│   ├── integrations/
│   └── decisions/
├── interfaces/
│   ├── msg/
│   ├── srv/
│   └── action/
├── asset_registry/
├── mission_orchestrator/
├── inspection_core/
├── inspection_skills/
├── evidence_store/
├── findings_service/
├── reporting_service/
├── robot_adapters/
├── integration_gateway/
├── operator_api/
├── operator_ui/
├── observability/
├── benchmark/
├── simulation/
├── deployment/
├── tools/
└── tests/
```

Document architectural decisions in:

```text
docs/decisions/ADR-XXXX-*.md
```

---

# 8. Standard Domain Models

All models must include `schema_version`.

## 8.1 Site

```yaml
site_id: string
name: string
timezone: string
map_id: string
coordinate_frame: string
status: ACTIVE | MAINTENANCE | DISABLED
metadata: object
```

## 8.2 Asset

```yaml
asset_id: string
site_id: string
name: string
asset_type: string
criticality: LOW | MEDIUM | HIGH | CRITICAL
location:
  frame_id: string
  position: [x, y, z]
  orientation: [x, y, z, w]
owner_team: string
inspection_profile_id: string
status: ACTIVE | OUT_OF_SERVICE | RETIRED
tags: [string]
metadata: object
```

## 8.3 Inspection profile

```yaml
inspection_profile_id: string
asset_type: string
required_skills: [string]
frequency:
  interval_seconds: integer
viewpoints:
  - viewpoint_id: string
    pose: object
    position_tolerance_m: float
    orientation_tolerance_rad: float
thresholds: object
escalation_policy_id: string
```

## 8.4 Robot

```yaml
robot_id: string
adapter_type: string
capabilities: [string]
sensors: [string]
payloads: [string]
battery:
  current_percent: float
  minimum_mission_percent: float
health:
  state: HEALTHY | DEGRADED | UNAVAILABLE
  reasons: [string]
```

## 8.5 Mission

```yaml
mission_id: string
site_id: string
mission_type: SCHEDULED | ON_DEMAND | FOLLOW_UP | VALIDATION
priority: integer
requested_assets: [string]
assigned_robot_id: string
state: CREATED | QUEUED | DISPATCHED | RUNNING | PAUSED | PARTIAL | COMPLETED | FAILED | CANCELLED | HELD
created_at: timestamp
started_at: timestamp
completed_at: timestamp
policy_version: string
```

## 8.6 Inspection result

```yaml
inspection_id: string
mission_id: string
asset_id: string
robot_id: string
skill_id: string
skill_version: string
timestamp: timestamp
status: NORMAL | WARNING | CRITICAL | INCONCLUSIVE | FAILED
confidence: float
measurements: object
evidence_ids: [string]
quality:
  overall: float
  issues: [string]
review_required: boolean
ground_truth: optional
```

## 8.7 Evidence

```yaml
evidence_id: string
inspection_id: string
asset_id: string
evidence_type: IMAGE | VIDEO | AUDIO | THERMAL | VIBRATION | LOG | POINT_CLOUD | OTHER
uri: string
hash: string
captured_at: timestamp
sensor_id: string
sensor_calibration_version: string
mime_type: string
size_bytes: integer
metadata: object
```

## 8.8 Finding

```yaml
finding_id: string
asset_id: string
origin_inspection_ids: [string]
category: string
severity: INFO | WARNING | CRITICAL
state: OPEN | ACKNOWLEDGED | ASSIGNED | REINSPECTION_REQUESTED | RESOLVED | CLOSED | REJECTED
title: string
description: string
confidence: float
assigned_to: optional
created_at: timestamp
updated_at: timestamp
resolution: optional
operator_feedback: optional
```

## 8.9 Audit event

```yaml
audit_id: string
timestamp: timestamp
actor_type: USER | SERVICE | ROBOT | SYSTEM
actor_id: string
action: string
resource_type: string
resource_id: string
before: optional
after: optional
trace_id: string
```

---

# 9. Inspection Skill Architecture

Create a common inspection skill interface.

## 9.1 Required lifecycle

1. Configuration validation
2. Sensor dependency validation
3. Asset compatibility check
4. Viewpoint quality check
5. Data acquisition
6. Data quality evaluation
7. Inference or rule evaluation
8. Confidence calculation
9. Evidence generation
10. Structured result output
11. Error reporting
12. Metrics emission

## 9.2 Conceptual interface

```cpp
class InspectionSkill {
public:
    virtual SkillMetadata metadata() const = 0;
    virtual ValidationResult validate_config(const SkillConfig&) = 0;
    virtual CapabilityRequirements requirements() const = 0;
    virtual InspectionResult execute(const InspectionContext&) = 0;
    virtual HealthStatus health() const = 0;
    virtual ~InspectionSkill() = default;
};
```

## 9.3 Initial non-production skills

### Visual condition skill

- RGB image capture
- Image quality score
- Blur detection
- Brightness validation
- Asset-region validation
- Rule-based or synthetic classification
- Annotated evidence

### Indicator state skill

- Detect configurable indicator colors/states
- Support synthetic benchmark fixtures
- Return `INCONCLUSIVE` when image quality is poor

### Gauge reading interface

- Implement API and synthetic/mock backend
- Include future real-model placeholder
- Never claim production accuracy

### Acoustic condition interface

- Implement ingestion, feature extraction hooks, and mock fixtures
- Add future dataset and validation notes

### Thermal inspection interface

- Define data contracts and simulation fixtures
- Do not claim calibrated temperature measurement without real hardware

### Generic external sensor skill

- Allow MQTT or ROS messages to provide measurements
- Support threshold-based findings

---

# 10. Asset-Centered Mission Planning

The system should accept requests such as:

```text
Inspect all due critical assets in Zone B.
```

The planner should determine:

- Which assets are due
- Which skills are required
- Which robots have required capabilities
- Which viewpoints are needed
- Route ordering
- Battery constraints
- Inspection priority
- Follow-up conditions

## Initial implementation

- Static asset configuration
- Simulated robot capabilities
- Deterministic route ordering
- Interfaces for future optimization
- Unit tests for asset selection and capability matching

---

# 11. Formal Mission State Machine

Suggested states:

```text
CREATED
  ↓
VALIDATING
  ↓
QUEUED
  ↓
DISPATCHED
  ↓
RUNNING
  ├── PAUSED
  ├── WAITING_FOR_OPERATOR
  ├── FOLLOW_UP_PENDING
  ├── PARTIAL
  ├── HELD
  ├── FAILED
  ├── CANCELLED
  └── COMPLETED
```

Required transitions:

- Startup validation failure
- Robot unavailable
- Navigation failure
- Inspection failure
- Sensor unavailable
- Battery low
- Network loss
- Operator pause
- Operator cancel
- Critical finding hold
- Follow-up inspection
- Resume after restart
- Partial completion

Every transition must be validated, logged, persisted, emitted as an event, include a reason, and be testable.

---

# 12. Robot Adapter Layer

## Required capabilities

- Robot identity
- Pose
- Battery
- Health
- Navigation goal
- Mission cancel
- Mission pause
- Teleoperation hook
- Docking hook
- Sensor inventory
- Capability list
- Current mission
- Localization status

## First adapter

- Existing ROS 2/Nav2 robot

## Second adapter

Implement one without requiring new hardware:

- Mock robot adapter
- Second simulated Nav2 namespace
- Replay adapter using recorded data

The goal is to prove the contract.

---

# 13. Evidence Management

## Required capabilities

- Unique evidence IDs
- SHA-256 hash
- Metadata sidecar
- Original and derived evidence distinction
- Capture timestamp
- Sensor identity
- Calibration version
- Skill/model version
- Mission, robot, site, and asset linkage
- Evidence quality score
- Storage quota handling
- Retention policy
- Export
- Missing evidence detection

## Storage backends

- Local filesystem
- Future object storage
- Test in-memory backend

If evidence writing fails:

- Mark inspection degraded or failed
- Emit an alert
- Record the reason
- Do not claim complete inspection success

---

# 14. Finding Lifecycle and Operator Workflow

## States

```text
OPEN
ACKNOWLEDGED
ASSIGNED
REINSPECTION_REQUESTED
RESOLVED
CLOSED
REJECTED
```

## Actions

- View finding
- View evidence
- Acknowledge
- Assign
- Comment
- Change severity with justification
- Mark false positive
- Request reinspection
- Record maintenance action
- Resolve
- Close
- Reopen

A reinspection request must create a linked mission with required skill, viewpoint, priority, due date, and reason.

---

# 15. Operator API and UI

## Minimum pages

- Site overview
- Robot status
- Mission queue
- Active mission
- Asset list
- Asset detail
- Findings queue
- Finding detail
- Evidence viewer
- Inspection history
- System health
- Configuration status
- Audit log

## API endpoints

```text
GET  /api/v1/sites
GET  /api/v1/assets
GET  /api/v1/assets/{id}
GET  /api/v1/missions
POST /api/v1/missions
POST /api/v1/missions/{id}/pause
POST /api/v1/missions/{id}/cancel
GET  /api/v1/findings
GET  /api/v1/findings/{id}
POST /api/v1/findings/{id}/acknowledge
POST /api/v1/findings/{id}/assign
POST /api/v1/findings/{id}/reinspect
POST /api/v1/findings/{id}/resolve
GET  /api/v1/evidence/{id}
GET  /api/v1/health
```

Generate an OpenAPI specification.

---

# 16. Persistence

Use SQLite initially with an abstraction for future PostgreSQL.

Persist:

- Sites
- Assets
- Inspection profiles
- Robots
- Missions
- Mission transitions
- Inspections
- Evidence metadata
- Findings
- Finding events
- Operator feedback
- Audit events
- Configuration versions
- System health events

Continue generating existing JSON, CSV, Markdown, and HTML reports as exports, but do not keep them as the only source of operational truth.

Requirements:

- Versioned migrations
- Migration tests
- Backup before migration
- Failure rollback
- Migration documentation

---

# 17. Event Architecture

Required normalized fields:

```yaml
event_id: string
event_type: string
schema_version: string
timestamp: timestamp
site_id: optional
robot_id: optional
mission_id: optional
asset_id: optional
inspection_id: optional
finding_id: optional
trace_id: string
payload: object
```

Required event types:

- Robot registered
- Robot health changed
- Mission created
- Mission state changed
- Waypoint reached
- Inspection started
- Inspection completed
- Inspection failed
- Evidence stored
- Finding created
- Finding updated
- Operator action
- Integration delivery failed
- System health changed

Use the event model for logging, auditability, replay, analytics, and future message brokers.

---

# 18. External Integration Gateway

## Initial integrations

- MQTT publishing
- MQTT measurement ingestion
- Generic webhook delivery
- Generic REST connector
- CSV import/export compatibility

## Future contracts

- OPC UA
- WMS/WES
- CMMS/EAM
- PLC data
- Network monitoring
- Ticketing

## Delivery reliability

- Retry
- Exponential backoff
- Idempotency key
- Delivery status
- Dead-letter storage
- Manual replay
- Error visibility

---

# 19. Synthetic and Simulated Data Strategy

## Scenario manifest

```yaml
scenario_id: string
seed: integer
world_version: string
robot_config: string
asset_states:
  conveyor_01: NORMAL
  motor_02: WARNING
  door_01: CRITICAL
ground_truth:
  - asset_id: motor_02
    category: ROLLER_IMBALANCE
    severity: WARNING
environment:
  lighting: NORMAL
  occlusion: NONE
  camera_noise: LOW
  network_faults: []
```

The inspection system must not directly read ground-truth labels during normal execution. Only the evaluator may compare predictions with ground truth afterward.

## Dataset manifest

```yaml
dataset_id: benchmark_v1
created_at: timestamp
source: SIMULATION
license: internal
samples:
  - sample_id: ...
    asset_id: ...
    label: ...
    evidence_uri: ...
split:
  train: []
  validation: []
  test: []
```

Prepare future fields for consent, source, anonymization, calibration, labeling method, reviewer, label confidence, usage restrictions, and retention.

---

# 20. Benchmark and Metrics Framework

## Navigation

- Mission completion rate
- Checkpoint reach rate
- Time per checkpoint
- Recovery count
- Navigation failure rate
- Position tolerance compliance
- Orientation tolerance compliance

## Inspection

- Capture success rate
- Evidence quality pass rate
- Precision
- Recall
- F1
- False warning rate
- False critical rate
- Inconclusive rate
- Skill latency

## Mission policy

- Correct continue decision
- Correct follow-up decision
- Correct hold decision
- Missed escalation
- Unnecessary escalation

## Evidence

- Completeness
- Hash success
- Asset linkage correctness
- Duplicate evidence
- Missing files

## Reliability

- Process restarts
- Mission recovery success
- Database recovery
- Network interruption recovery
- Disk pressure behavior

## Operator workflow

- Time to acknowledge
- Time to resolve
- Findings without owner
- Reinspection completion
- False-positive feedback rate

Generate JSON, CSV, Markdown, HTML, and machine-readable pass/fail outputs.

CI must fail when critical benchmark metrics regress, required evidence disappears, mission transitions become invalid, schema compatibility breaks, or launch smoke tests fail.

---

# 21. Fault Injection

Implement reproducible faults:

- Blocked path
- Robot stuck
- Navigation timeout
- Localization jump
- Sensor unavailable
- Blurred camera
- Dark image
- Missing asset
- Corrupted evidence
- Network interruption
- Database unavailable
- Disk-full simulation
- Node crash
- Low battery
- MQTT delivery failure

Every fault requires a stable ID, configuration switch, deterministic seed where applicable, expected behavior, integration test, and recovery-matrix entry.

Create:

```text
docs/operations/recovery_matrix.md
```

---

# 22. Reliability and Resilience

Required:

- Node health reporting
- Heartbeats
- Watchdogs
- Startup dependency validation
- Graceful shutdown
- Persistent mission state
- Resume after restart
- Idempotent report generation
- Atomic writes
- Storage monitoring
- Time synchronization checks
- Duplicate-event protection
- Backpressure handling

## Endurance testing

Initial:

- 8-hour simulation
- Repeated patrol rounds
- Accelerated timing option
- Memory, CPU, disk, error, and mission monitoring

Future:

- 24 hours
- 72 hours
- 7 days
- Physical-site endurance

Do not claim future targets until completed.

---

# 23. Observability

## Logs

- Structured JSON
- Severity
- Trace ID
- Mission ID
- Asset ID
- Robot ID
- No secrets
- Configurable retention

## Metrics

- Mission counts
- Mission duration
- Inspection latency
- Findings
- Failures
- Robot health
- Evidence failures
- Queue depth
- Integration failures
- Database latency
- Resource usage

Use Prometheus-compatible output if practical.

## Health endpoints

```text
/health/live
/health/ready
/health/details
```

---

# 24. Security Program

Add:

- `SECURITY.md`
- Threat model
- Secure deployment guide
- Incident response guide
- Secret-management guide
- Dependency update policy

## Authentication

Provide a development mode and production-ready OIDC/OAuth-compatible interface. Do not invent custom password cryptography.

## Roles

- Viewer
- Operator
- Maintenance
- Administrator
- Service integration

Enforce permissions server-side.

## Audit

Audit login, configuration changes, mission commands, finding state changes, evidence access, user management, and integration configuration.

## Supply chain

CI should include:

- Dependency vulnerability scan
- Static analysis
- Secret scan
- License inventory
- SBOM generation
- Container scan
- Signed release artifact plan

## Data protection

Make evidence/log retention, export, deletion, site isolation, user access, and data minimization configurable.

---

# 25. Deployment Architecture

## Initial target

Single-site edge deployment:

```text
edge host
├── ROS 2 runtime
├── mission services
├── inspection services
├── database
├── operator API
├── operator UI
├── integration gateway
├── evidence storage
└── observability
```

## Environment profiles

- Development
- CI
- Simulation
- Demo
- Edge pilot
- Production

## Configuration

- Schema validation
- Safe defaults
- Environment overrides
- No plaintext secrets
- Config version
- Config diff
- Config rollback
- Fail startup on invalid critical config

## Backup and restore

- Database backup
- Evidence metadata backup
- Configuration backup
- Restore verification
- Documented procedure

## Updates

- Versioned releases
- Database migrations
- Rollback
- Compatibility matrix
- Release notes
- Post-update health verification

---

# 26. CI/CD

Required stages:

1. Format
2. Lint
3. Static analysis
4. Unit tests
5. Schema validation
6. Build
7. Integration tests
8. Launch smoke tests
9. Simulation benchmark
10. Security scans
11. Package/container build
12. Artifact publishing

Publish test results, coverage, benchmark reports, logs, screenshots, reports, SBOM, and security summary.

---

# 27. Testing Strategy

## Unit tests

- State transitions
- Asset selection
- Capability matching
- Threshold evaluation
- Confidence policy
- Finding lifecycle
- Evidence hashing
- Retry logic
- Schema validation
- Permission checks

## Integration tests

- Mission to inspection
- Inspection to finding
- Finding to report
- Operator action to reinspection
- MQTT measurement to finding
- Persistence
- Process restart
- Evidence storage failure
- Robot adapter failure

## Launch tests

- Existing benchmark launch
- New platform launch
- Missing dependency
- Invalid config
- Multi-namespace simulation

## End-to-end scenarios

1. Normal patrol
2. Warning finding
3. Critical finding
4. Inconclusive inspection
5. Navigation failure
6. Sensor failure
7. Operator reinspection
8. Restart during mission
9. External sensor measurement
10. Integration delivery failure

Protect message schemas, export schemas, API versions, config versions, and existing launch usage.

---

# 28. Model and Rule Governance

## Model registry

Track:

- Model ID
- Version
- Skill
- Training dataset
- Evaluation dataset
- Metrics
- Thresholds
- Deployment date
- Status
- Rollback version

## Rule registry

Track:

- Rule ID
- Version
- Description
- Applicable asset types
- Thresholds
- Severity mapping
- Test coverage
- Owner
- Approval status

## Inference trace

Each result must record:

- Model/rule version
- Inputs
- Quality checks
- Output
- Confidence
- Threshold
- Final status
- Post-processing

## Future production gate

Before production claims:

- Real representative data
- Independent test set
- Documented labeling
- False-negative analysis
- False-critical analysis
- Environment robustness
- Calibration evaluation
- Human review
- Approval record

---

# 29. Historical Analytics

Build now:

- Inspection counts
- Finding counts
- Findings per asset
- Repeated findings
- Time between findings
- Severity history
- Mission completion trend
- Inspection coverage
- Review backlog
- Mean acknowledgement time
- Mean resolution time

Prepare interfaces for future baseline modeling, trend detection, remaining useful life, cross-asset comparison, similar incident retrieval, and maintenance-effectiveness analysis. Label these experimental until validated.

---

# 30. Product Maturity Labels

Use:

- `CONCEPT`
- `MOCK`
- `SIMULATION_VALIDATED`
- `LAB_VALIDATED`
- `PILOT_VALIDATED`
- `PRODUCTION_VALIDATED`

Examples:

```yaml
capability: gas_leak_detection
maturity: MOCK
notes: Workflow placeholder only; no real gas sensor validation.
```

```yaml
capability: nav2_waypoint_patrol
maturity: SIMULATION_VALIDATED
notes: Requires physical endurance and recovery testing.
```

Expose maturity in documentation and demo materials.

---

# 31. Product Documentation

## User

- Product overview
- Quick start
- Simulation guide
- Operator guide
- Finding workflow
- Asset configuration
- Mission configuration
- Troubleshooting

## Developer

- Architecture
- Package map
- Interfaces
- Build
- Testing
- Adding an inspection skill
- Adding a robot adapter
- Adding an integration
- Database schema
- API specification

## Operations

- Installation
- Configuration
- Backup
- Restore
- Update
- Rollback
- Monitoring
- Incident response
- Recovery matrix

## Security

- Threat model
- Authentication
- Authorization
- Secret management
- Data retention
- Vulnerability reporting

## Product

- Capability matrix
- Maturity matrix
- Known limitations
- Future real-data validation plan
- Pilot-readiness checklist

---

# 32. Future Real-World Validation Plan

## Stage A: Laboratory data

- One real physical asset
- Normal and abnormal states
- Repeated measurements
- Controlled ground truth
- Lighting variation
- Viewpoint variation
- Noise variation
- Dataset documentation

## Stage B: Physical robot

- Real robot
- Real navigation
- Repeatable viewpoint
- At least 30 missions
- Failure recovery
- Operator interaction

## Stage C: Design partner

- Customer-approved use case
- Data access agreement
- Site requirements
- Security requirements
- Baseline process
- Success metrics
- Pilot scope

## Stage D: Pilot metrics

- Inspection coverage
- Operator time saved
- Detection lead time
- False alarms
- Missed findings
- Mean time to acknowledge
- Mean time to act
- Repeated fault detection
- Support burden
- System uptime

## Stage E: Production gates

- Security approval
- Legal review
- Data protection
- Deployment support
- SLA
- Monitoring
- Update process
- Incident response
- Customer training
- Commercial agreement

---

# 33. Regulatory and Safety Considerations

Do not claim certification.

Prepare for future review of:

- Machine safety boundaries
- Robot vendor safety requirements
- Industrial site rules
- Data protection
- Cybersecurity
- AI transparency
- Evidence retention
- Liability
- Hazardous-area restrictions
- Sensor certification
- Human oversight

Remain advisory by default. Do not directly control safety-critical machinery without a separate safety architecture and professional review.

---

# 34. Startup Operations Requirements

## Customer onboarding

- Site discovery
- Asset import
- Robot integration
- Inspection-profile setup
- User setup
- Training
- Acceptance test

## Support

- Diagnostic bundle
- Remote log export
- Health report
- Version inventory
- Reproduction steps
- Support ticket linkage

## SLA preparation

Track:

- Service availability
- Mission execution availability
- Data loss
- Support response
- Update success
- Critical defect rate

## Commercial packaging — future

- Simulation/demo
- Single-site edge
- Multi-site enterprise
- Integrator edition
- Developer SDK

Do not implement pricing logic in core software.

---

# 35. Definition of 100/100 Engineering Foundation

## Architecture

- Domain boundaries documented
- State machines explicit
- Interfaces versioned
- Robot adapter implemented
- Inspection skill framework implemented
- Asset-centered planning implemented

## Functionality

- Full finding lifecycle
- Operator UI
- Asset registry
- Mission scheduling
- Evidence traceability
- Historical views
- External integration gateway
- Reinspection flow

## Reliability

- Persistent state
- Restart recovery
- Fault injection
- Endurance test
- Health monitoring
- Recovery matrix
- Backups
- Update rollback

## Quality

- Unit tests
- Integration tests
- Launch tests
- End-to-end tests
- Benchmark framework
- Regression gates
- Documentation
- Code-quality checks

## Security

- Authentication
- Authorization
- Audit log
- Secret handling
- Vulnerability scans
- SBOM
- Secure configuration
- Retention controls

## Deployment

- Reproducible deployment
- Environment profiles
- Versioned release
- Configuration validation
- Migration system
- Backup and restore
- Operational documentation

## Transparency

- Capability maturity labels
- Known limitations
- No fabricated production claims
- Future real-data validation gates
- Measured benchmark output

Commercial readiness still requires customer, field, legal, and operational evidence.

---

# 36. Implementation Phases

## Phase 0: Repository audit

Deliver:

- Current architecture documents
- Package dependency graph
- Existing test inventory
- Existing output schemas
- Current risks
- Proposed migration plan
- Baseline benchmark

Acceptance:

- Existing project still builds and runs
- No functional change required

## Phase 1: Foundations

Implement:

- Shared interfaces
- Schema versioning
- IDs and timestamps
- Event model
- Structured logs
- Configuration validation
- Initial database
- Compatibility export layer

Acceptance:

- Existing patrol persists missions, inspections, evidence metadata, and findings

## Phase 2: Asset-centered model

Implement:

- Site
- Asset registry
- Inspection profiles
- Viewpoints
- Asset-driven mission generation

Acceptance:

- Mission can be created by selecting assets rather than manually specifying only route checkpoints

## Phase 3: Inspection skill framework

Implement:

- Common skill interface
- Visual skill migration
- External measurement skill
- Quality checks
- Rule/model metadata
- Synthetic fixtures

Acceptance:

- Existing inspection behavior runs through the new skill interface

## Phase 4: Finding workflow

Implement:

- Finding lifecycle
- Operator actions
- Reinspection
- Audit events
- Persistence

Acceptance:

- A warning/critical inspection creates a finding that can be acknowledged, assigned, reinspected, resolved, and closed

## Phase 5: Operator API and UI

Implement:

- Versioned API
- OpenAPI
- Site dashboard
- Mission page
- Asset page
- Findings queue
- Evidence viewer
- Health page

Acceptance:

- Full workflow can be completed without manually opening generated files

## Phase 6: Robot adapter

Implement:

- Nav2 adapter
- Mock adapter
- Capability model
- Robot health
- Adapter tests

Acceptance:

- Mission orchestration does not call Nav2-specific interfaces directly outside the adapter

## Phase 7: Integrations

Implement:

- MQTT
- Webhook
- Retry
- Dead-letter
- External measurement ingestion

Acceptance:

- Synthetic sensor data can create/enrich a finding
- A finding can be reliably delivered to a mock external system

## Phase 8: Reliability

Implement:

- Watchdogs
- Restart recovery
- Fault injection
- Recovery matrix
- Endurance test
- Storage monitoring

Acceptance:

- Required fault scenarios produce documented, testable behavior

## Phase 9: Security and deployment

Implement:

- Authentication
- Roles
- Audit
- Secret handling
- Containers
- Backup/restore
- Release pipeline
- SBOM
- Security scans

Acceptance:

- A secure edge-demo deployment can be reproduced from documentation

## Phase 10: Product-readiness package

Deliver:

- Capability matrix
- Maturity matrix
- Pilot checklist
- Demo scenario
- Benchmark report
- Architecture diagram
- Operator guide
- Deployment guide
- Future real-data plan

Acceptance:

- A technical evaluator can reproduce the system, inspect limitations, and identify what remains for a real pilot

---

# 37. Immediate Coding Order

1. Audit current repository.
2. Establish one reproducible baseline test.
3. Add IDs and schema versions.
4. Add persistence without removing existing files.
5. Formalize the finding model.
6. Build the asset registry.
7. Introduce the inspection skill interface.
8. Add benchmark evaluator with ground-truth separation.
9. Build minimal operator API.
10. Build minimal operator UI.

---

# 38. Codex Working Instructions

## Before coding

1. Read the repository.
2. Build it.
3. Run existing tests.
4. Identify package names.
5. Identify the exact ROS 2 distribution.
6. Identify language standards.
7. Identify current message definitions.
8. Identify report schemas.
9. Identify backward-compatibility requirements.
10. Write a short implementation plan.

## During coding

- Make small logical patches
- Preserve existing launch behavior
- Add tests with each feature
- Update documentation
- Avoid unrelated refactoring
- Avoid unnecessary dependencies
- Validate external input
- Provide clear failure messages
- Add feature flags for incomplete modules

## After each phase

1. Build
2. Run unit tests
3. Run integration tests
4. Run launch smoke test
5. Run benchmark
6. Compare with baseline
7. Update known limitations
8. Update changelog
9. Produce a phase report

## Never do

- Never fabricate benchmark results
- Never label mock perception as production AI
- Never expose secrets
- Never bypass safety logic
- Never silently change schemas
- Never delete working functionality without migration
- Never make safety-critical control claims
- Never hardcode customer logic into the core
- Never create unnecessary microservices
- Never use an LLM as a substitute for deterministic system design

---

# 39. Phase Report Template

Create:

```text
docs/phase_reports/phase_XX_report.md
```

Template:

```markdown
# Phase X Report

## Scope

## Changes

## Files Added

## Files Modified

## Interfaces Added or Changed

## Tests

## Benchmark Results

## Backward Compatibility

## Known Limitations

## Risks

## Next Phase

## Reproduction Commands
```

---

# 40. Acceptance Checklist

## Product core

- [ ] Site model
- [ ] Asset registry
- [ ] Inspection profiles
- [ ] Asset-driven mission planning
- [ ] Mission state machine
- [ ] Robot adapter
- [ ] Inspection skill registry
- [ ] Evidence registry
- [ ] Finding lifecycle
- [ ] Operator workflow
- [ ] Historical analytics

## Data

- [ ] Schema versions
- [ ] Persistent database
- [ ] Migrations
- [ ] Export compatibility
- [ ] Event model
- [ ] Audit model
- [ ] Dataset manifests
- [ ] Ground-truth separation

## Reliability

- [ ] Health checks
- [ ] Watchdogs
- [ ] Restart recovery
- [ ] Fault injection
- [ ] Recovery matrix
- [ ] Long-duration test
- [ ] Disk monitoring
- [ ] Network failure handling

## Integrations

- [ ] MQTT
- [ ] Webhooks
- [ ] Retry
- [ ] Dead-letter
- [ ] External measurement
- [ ] Future OPC UA contract
- [ ] Future CMMS/EAM contract
- [ ] Future WMS/WES contract

## Security

- [ ] Authentication
- [ ] Authorization
- [ ] Audit log
- [ ] Secret management
- [ ] Threat model
- [ ] Vulnerability scanning
- [ ] SBOM
- [ ] Retention policy

## Deployment

- [ ] Environment profiles
- [ ] Container strategy
- [ ] Config validation
- [ ] Backup
- [ ] Restore
- [ ] Update
- [ ] Rollback
- [ ] Release process

## Quality

- [ ] Unit tests
- [ ] Integration tests
- [ ] Launch tests
- [ ] End-to-end scenarios
- [ ] Benchmark
- [ ] Regression gate
- [ ] Static analysis
- [ ] Documentation

## Future external validation

- [ ] Real asset
- [ ] Real sensor data
- [ ] Real robot
- [ ] Lab benchmark
- [ ] Design partner
- [ ] Pilot
- [ ] ROI measurement
- [ ] Security review
- [ ] Legal review
- [ ] Production approval

---

# 41. Final Implementation Objective

The completed repository should tell this truthful story:

> This platform provides a modular, asset-centered autonomous inspection workflow with mission orchestration, robot abstraction, inspection skills, evidence traceability, findings management, operator review, external integrations, secure edge deployment, automated benchmarks, fault recovery, and transparent capability maturity. Current perception and field-performance claims remain simulation- or lab-scoped until validated with real industrial data.

The project should no longer appear to be only:

- A Gazebo demonstration
- A Nav2 waypoint project
- An image classifier
- A report generator

It should become:

> A complete industrial inspection product foundation technically prepared for real sensor integration, laboratory validation, design-partner deployment, and future commercial pilots.

---

# 42. First Command to Codex

```text
Read ADVANCE.md and audit the complete repository before modifying anything. Build and run the existing project, document the current architecture and baseline behavior, identify the exact gap between the repository and Phase 0 requirements, and then implement only Phase 0. Preserve all existing behavior. Create the required architecture documents, baseline test command, test inventory, technical-debt list, and Phase 0 report. Do not start Phase 1 until Phase 0 is complete and all existing functionality still builds and runs.
```
