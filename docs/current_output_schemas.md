# Current Output Schemas

This document records the current configuration and export contracts as of **Saturday, July 18, 2026**.

The big idea is simple:

- configuration files describe the site, assets, and inspection expectations
- the benchmark generator turns those into a concrete patrol scenario
- runtime nodes emit evidence and reports with explicit schema versions

That gives us a cleaner product foundation than a pure hardcoded benchmark.

## Why Schema Versions Exist

Schema versions matter because they let us change the system without silently breaking:

- downstream analysis scripts
- future persistence layers
- startup dashboards
- operator tooling
- compatibility checks in CI later

Think of a schema version like a drawing revision number in a factory. It tells everyone which contract they are looking at.

## Configuration Schemas

### Site config

File:

- [`benchmark_site.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/sites/benchmark_site.yaml)

Current schema:

- `site.v1`

Purpose:

- identify the site
- declare map and frame context
- describe the simulated environment

## Asset registry schema

File:

- [`benchmark_asset_registry.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml)

Current schema:

- `asset_registry.v1`

Purpose:

- declare benchmark assets
- assign owner team and criticality
- map each asset to a checkpoint and viewpoint
- carry tolerance metadata needed for repeatable inspection

Important current fields:

- `asset_id`
- `asset_type`
- `zone`
- `criticality`
- `owner_team`
- `inspection_profile_id`
- `enabled_modalities`
- `tags`
- `checkpoint.name`
- `checkpoint.x`
- `checkpoint.y`
- `checkpoint.yaw`
- `checkpoint.viewpoint_id`
- `checkpoint.position_tolerance_m`
- `checkpoint.orientation_tolerance_rad`

## Inspection profile schema

File:

- [`benchmark_inspection_profiles.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml)

Current schema:

- `inspection_profile.v1`

Purpose:

- define what kind of inspection a class of asset expects
- describe required skills and thresholds
- declare inspection frequency hints

Important current fields:

- `inspection_profile_id`
- `asset_type`
- `required_skills`
- `frequency.interval_seconds`
- `viewpoints`
- `thresholds`
- `escalation_policy_id`

## Generated Scenario Schemas

These files are written under:

- `/home/samarth/.ros/factory_inspection/benchmark/scenario`

### Generated checkpoint config

File:

- `generated_checkpoints.yaml`

Current schema:

- `benchmark_checkpoint_config.v2`

Purpose:

- define the concrete patrol order for the current run
- embed site context and enriched asset metadata

Important top-level fields:

- `schema_version`
- `site_id`
- `site_name`
- `site_timezone`
- `coordinate_frame`
- `asset_registry_file`
- `site_config_file`
- `inspection_profiles_file`

Important checkpoint-level fields:

- `name`
- `asset_id`
- `criticality`
- `owner_team`
- `inspection_profile_id`
- `asset_status`
- `asset_tags`
- `viewpoint_id`
- `position_tolerance_m`
- `orientation_tolerance_rad`

### Ground truth file

File:

- `ground_truth.yaml`

Current schema:

- `benchmark_ground_truth.v2`

Purpose:

- record the synthetic truth used by the benchmark
- keep run metadata tied to site/config context

### Scenario manifest

File:

- `scenario_manifest.json`

Current schema:

- `benchmark_scenario_manifest.v2`

Purpose:

- summarize the generated scenario in one machine-readable document
- record seed, selected assets, site details, and config provenance

Important fields:

- `schema_version`
- `scenario_id`
- `seed`
- `site`
- `asset_registry_file`
- `site_config_file`
- `inspection_profiles_file`
- `selected_asset_records`

## Runtime Report Schemas

These files are written under:

- `/home/samarth/.ros/factory_inspection/benchmark`

### Round report

Files:

- `latest_report.json`
- `round_000X_report.json`

Current schema:

- `round_report.v2`

Purpose:

- record one round summary, mission decision, and per-checkpoint findings

### Dashboard state

File:

- `latest_dashboard_state.json`

Current schema:

- `dashboard_state.v2`

Purpose:

- drive a dashboard-friendly summary of current run state

### Campaign state

File:

- `latest_campaign_state.json`

Current schema:

- `campaign_state.v2`

Purpose:

- preserve cross-round mission state and follow-up history

## CSV And Human-Readable Outputs

Current files include:

- `inspection_log.csv`
- `asset_history.csv`
- `latest_report.md`
- `latest_dashboard.html`
- `round_000X_report.md`
- `round_000X_report.html`

Current status:

- these are still file-based exports rather than database-backed products
- the CSV files do not yet embed explicit `schema_version` fields
- today the column headers are the practical contract

That is acceptable for the current benchmark stage, but it is an obvious next hardening step for later product phases.

## Code Sources For These Schemas

Primary files:

- [`benchmark_scenario_generator.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)
- [`benchmark_patrol.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_patrol.launch.py)
- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)

In plain words:

- the launch file passes the config sources in
- the scenario generator emits schema-versioned scenario artifacts
- the report node emits schema-versioned runtime summaries
