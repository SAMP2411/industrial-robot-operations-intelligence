# Current Risks And Migration Plan

This document captures the main current engineering risks and the recommended migration direction as of **Saturday, July 18, 2026**.

## Current Risks

### 1. Product truth is file-based

Risk:

- reports, YAML configs, and CSV files are useful exports, but there is no persistent database-backed operational truth

Impact:

- harder future operator workflow
- harder auditability
- harder reinspection and finding lifecycle support

### 2. Scenario assets are still benchmark-oriented

Risk:

- the benchmark now has a real YAML asset registry and inspection-profile layer, but the data model is still optimized for simulation rather than long-term product administration

Impact:

- harder transition to asset-centered planning
- harder reuse across sites and robots

### 3. Testing depth is limited

Risk:

- current verification leans on smoke/regression scripts and manual checking

Impact:

- future refactors become riskier
- interface and schema regressions can slip through

### 4. Operator workflow is missing

Risk:

- findings are generated, but not lifecycle-managed through operator actions

Impact:

- the system can detect, but not yet fully manage, operational work

### 5. Fleet/platform abstractions are incomplete

Risk:

- code already points toward multiple robot profiles and fleet behavior, but the contract is not fully stabilized

Impact:

- future scaling could become messy if abstraction is not formalized

## Recommended Migration Direction

### Phase 0

- document current architecture
- preserve the working benchmark
- establish reproducible baseline tests

### Phase 1

- add schema versions, stronger IDs, and persistence-friendly record structure
- preserve existing JSON/CSV/HTML export compatibility

Current status:

- partially complete
- scenario outputs and key JSON reports now carry explicit schema versions
- config provenance is now preserved in generated scenario artifacts

### Phase 2

- introduce a proper persistent asset registry and inspection-profile source of truth
- move mission generation from route-first toward asset-first

Current status:

- seeded in benchmark form through YAML config files
- not yet elevated into a service-backed or database-backed product layer

### Phase 3

- formalize inspection skills and evidence quality contracts

### Phase 4

- add finding lifecycle and operator workflow

### Phase 5

- add operator API/UI

### Phase 6+

- robot adapter hardening
- integrations
- resilience
- security
- deployment packaging

## Migration Rule

The safest path is:

- keep the working single-robot benchmark alive
- add new product layers beside it
- keep compatibility exports during migration
- avoid rewriting everything into a giant “platform” node
