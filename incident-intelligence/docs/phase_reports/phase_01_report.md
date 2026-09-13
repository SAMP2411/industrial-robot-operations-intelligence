# Phase 1 Report

## Scope

Implement the first product-foundation slice after the Phase 0 audit, aligned with [`advance.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/advance.md), while preserving the working single-robot benchmark.

## Changes

- added a config-backed benchmark site definition
- added a config-backed benchmark asset registry
- added config-backed benchmark inspection profiles
- updated the benchmark launch path to pass those config sources into scenario generation
- enriched generated checkpoint and scenario outputs with site and asset metadata
- added explicit schema versions to key JSON report exports
- updated the startup handoff and audit docs to match the new architecture

## Files Added

- [`benchmark_site.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/sites/benchmark_site.yaml)
- [`benchmark_asset_registry.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml)
- [`benchmark_inspection_profiles.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml)
- [`current_output_schemas.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_output_schemas.md)
- [`phase_01_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/phase_reports/phase_01_report.md)

## Files Modified

- [`benchmark_patrol.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_patrol.launch.py)
- [`benchmark_scenario_generator.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)
- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)
- [`README.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/README.md)
- [`STARTUP_CONTEXT_SUMMARY.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/STARTUP_CONTEXT_SUMMARY.md)
- [`current_architecture.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_architecture.md)
- [`current_data_outputs.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_data_outputs.md)
- [`current_known_limitations.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_known_limitations.md)
- [`current_launch_flow.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_launch_flow.md)
- [`current_risks_and_migration_plan.md`](/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/docs/current_risks_and_migration_plan.md)

## Interfaces Added or Changed

### New config interfaces

- `site.v1`
- `asset_registry.v1`
- `inspection_profile.v1`

### Changed generated scenario interfaces

- `generated_checkpoints.yaml` now uses `benchmark_checkpoint_config.v2`
- `ground_truth.yaml` now uses `benchmark_ground_truth.v2`
- `scenario_manifest.json` now uses `benchmark_scenario_manifest.v2`

New scenario fields include:

- site metadata
- config provenance paths
- asset criticality
- owner team
- inspection profile ID
- viewpoint ID
- position/orientation tolerances

### Changed runtime report interfaces

- `latest_report.json` and `round_000X_report.json` now use `round_report.v2`
- `latest_dashboard_state.json` now uses `dashboard_state.v2`
- `latest_campaign_state.json` now uses `campaign_state.v2`

## Tests

Verified on **Saturday, July 18, 2026** with:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
python3 -m py_compile \
  legacy/autonomy_demo/ros2_ws/src/factory_inspection_mission/launch/benchmark_scenario_generator.py \
  legacy/autonomy_demo/ros2_ws/src/factory_inspection_mission/launch/benchmark_patrol.launch.py

source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  factory_inspection_interfaces \
  factory_inspection_mission
```

Smoke-test verification:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
./legacy/autonomy_demo/tools/clean_benchmark_runtime.sh
./legacy/autonomy_demo/tools/run_iteration_smoke_test.sh
```

Targeted full export verification:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
export FACTORY_SCENARIO_SEED=4242
export FACTORY_SCENARIO_ALLOW_CRITICAL=false
export FACTORY_TARGET_ASSETS=CNV-510
export FACTORY_BENCHMARK_SUCCESS_PATTERN='Wrote round 1 report'
export FACTORY_BENCHMARK_TIMEOUT_SECONDS=180
./legacy/autonomy_demo/tools/run_benchmark_with_retry.sh headless:=True use_rviz:=False
```

## Benchmark Results

Smoke-test route-health log:

- [`benchmark_attempt_20260719_022649_1.log`](/home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260719_022649_1.log)

Observed proof points:

- managed nodes reached active state
- Nav2 accepted patrol round 1
- robot progressed to checkpoint `6/10: mid_east_service_bay`

Targeted full-export log:

- [`benchmark_attempt_20260719_021816_3.log`](/home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260719_021816_3.log)

Observed proof points:

- JSON report path completed successfully
- `latest_report.json` contained `round_report.v2`
- `latest_dashboard_state.json` contained `dashboard_state.v2`
- `latest_campaign_state.json` contained `campaign_state.v2`
- scenario artifacts preserved site/config provenance

Note:

- the runtime filenames in this environment include `20260719`
- the project notes remain anchored to **Saturday, July 18, 2026**

## Backward Compatibility

- the top-level benchmark launch command remains the same
- the single-robot benchmark flow remains intact
- scenario generation retains compatibility fallback behavior through default values and legacy in-code profiles
- existing JSON/CSV/HTML export families were preserved rather than replaced

## Known Limitations

- the new asset and inspection-profile truth is still YAML-based, not database-backed
- the mission flow is still primarily route-first, even though it now carries richer asset metadata
- CSV exports still behave as file contracts rather than schema-versioned records
- there is still no operator API/UI or finding lifecycle

## Risks

- file-based truth can drift without stronger validation and persistence
- richer schemas increase future compatibility burden if not protected by tests
- the benchmark is still simulation-oriented even though the data model is becoming more product-shaped

## Next Phase

- formalize persistent asset, mission, evidence, and finding models
- move from benchmark asset registry files toward a real product source of truth
- add a finding model and operator workflow contracts

## Reproduction Commands

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
  factory_inspection_interfaces \
  factory_inspection_mission
source /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/install/setup.bash
./legacy/autonomy_demo/tools/clean_benchmark_runtime.sh
./legacy/autonomy_demo/tools/run_iteration_smoke_test.sh
```
