# Current Data Outputs

This document records the outputs currently produced by the repository as of **Saturday, July 18, 2026**.

## Runtime Output Root

Most runtime artifacts are written to:

- `/home/samarth/.ros/factory_inspection/benchmark`

## Scenario Generation Outputs

Written under:

- `/home/samarth/.ros/factory_inspection/benchmark/scenario`

Current files:

- `generated_world.sdf`
- `generated_checkpoints.yaml`
- `ground_truth.yaml`
- `scenario_manifest.json`

Purpose:

- define the current benchmark world
- define the route and asset mapping
- define ground-truth benchmark conditions

Current improvement:

- these files now carry explicit site/config provenance and schema-versioned contracts
- the checkpoint file now includes product-facing asset metadata such as `criticality`, `owner_team`, `inspection_profile_id`, `viewpoint_id`, and tolerance values

## Evidence Outputs

Current inspection runs generate:

- raw checkpoint images
- annotated checkpoint images

Examples from the July 18, 2026 smoke-test run:

- `0000_spawn_lane_roller_imbalance_4815000000_raw.png`
- `0000_spawn_lane_roller_imbalance_4815000000_annotated.png`
- `0002_upper_right_turn_gas_leak_detected_23148000000_annotated.png`

Purpose:

- preserve visual evidence
- show what label/severity the inspection pipeline produced

## Structured Export Outputs

Current export artifacts include:

- `inspection_log.csv`
- `latest_report.json`
- `latest_report.md`
- `latest_dashboard.html`
- `latest_dashboard_state.json`
- `latest_campaign_state.json`
- `asset_history.csv`
- `round_000X_report.json`
- `round_000X_report.md`
- `round_000X_report.html`

Purpose:

- inspection log for tabular review
- per-round structured reporting
- human-readable summaries
- dashboard-style visualization exports
- run and campaign history

Current improvement:

- `latest_report.json` and `round_000X_report.json` now use `round_report.v2`
- `latest_dashboard_state.json` now uses `dashboard_state.v2`
- `latest_campaign_state.json` now uses `campaign_state.v2`

## Current Operational Truth

Important current limitation:

- JSON/CSV/HTML exports are currently the main stored outputs
- there is no repository-local database-backed operational store yet

That means the repository already has strong export behavior, but not yet a persistent product database.

## Schema Reference

The detailed schema map now lives in:

- [`current_output_schemas.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/current_output_schemas.md)

## Current Smoke-Test Proof

The most recent verified smoke test for route health succeeded with:

- log: [`benchmark_attempt_20260719_022649_1.log`](/home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260719_022649_1.log)

What it proved:

- Gazebo started
- Nav2 fully activated
- patrol round 1 was accepted
- checkpoint inspections were executed
- evidence images were written
- robot reached checkpoint `6/10: mid_east_service_bay`

What it did **not** prove:

- a fresh full-round `latest_report.json` write for that exact run

That distinction is intentional and now reflected by the smoke-test script wording.

## Current Full Export Proof

A targeted single-asset benchmark run also verified the JSON report export path with:

- log: [`benchmark_attempt_20260719_021816_3.log`](/home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260719_021816_3.log)

What it proved:

- the mission completed a report-writing path
- `latest_report.json` was written with `round_report.v2`
- `latest_dashboard_state.json` was written with `dashboard_state.v2`
- `latest_campaign_state.json` was written with `campaign_state.v2`
