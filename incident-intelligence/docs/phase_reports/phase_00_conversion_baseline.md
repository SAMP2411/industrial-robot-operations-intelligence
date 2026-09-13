# Phase 0: conversion baseline

- Baseline commit: `8954fb5`
- Baseline tag: `pre-conversion-baseline`
- Conversion branch: `startup-incident-intelligence`
- Repository was already initialized with preserved history; it was not reinitialized.

## Existing runtime

- Build: `colcon build --symlink-install --cmake-clean-cache --packages-select factory_inspection_interfaces factory_inspection_mission`
- Autonomy smoke test: `./legacy/autonomy_demo/tools/run_iteration_smoke_test.sh`
- Legacy API/UI: `uvicorn legacy.autonomy_demo.fleet_console.app.main:app --port 8000`
- Legacy SQLite default: `legacy/autonomy_demo/fleet_console/data/fleetwatch.db`
- Benchmark artifacts: `~/.ros/factory_inspection/benchmark`
- Operator queue: `~/.ros/factory_inspection/operator/operator_mission_queue.yaml`

The first pre-build smoke attempt failed because the copied `install/` did not contain the packages. The first build attempt then exposed copied CMake cache paths pointing at `/home/samarth/projects/industrial-robot-operations-intelligence`; `--cmake-clean-cache` corrected generated state without changing source. Both ROS packages subsequently built, and the smoke test passed on its first runtime attempt with progress through checkpoint 6/10. Existing FleetWatch pytest passed. Generated JSON/HTML/evidence and SQLite/operator workflows remain part of the legacy autonomy demo.
