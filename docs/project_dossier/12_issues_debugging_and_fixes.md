# Issues, Debugging, And Fixes

## 1. Nav2 Not Ready Yet

### Symptom

- patrol mission sends a round request
- waypoint follower rejects the goal because the action server is inactive

### Why It Happened

Nav2 lifecycle nodes were still activating during early launch.

### Fix

- keep the mission node tolerant to early rejection
- retry after a short delay instead of failing fast

### Lesson

Robotics bringup is often asynchronous. Startup resilience matters.

## 2. TF Startup Warnings

### Symptom

- controller or planner logs missing transforms such as `odom` or `map`

### Why It Happened

The sim and localization pipeline were still warming up.

### Fix

- allow Nav2 lifecycle activation to finish
- do not treat all startup TF warnings as fatal
- only treat them as blockers if they persist and navigation never activates

### Lesson

Some launch-time warnings are normal during bringup. The real question is whether the system converges.

## 3. Interrupted Runs Causing Dirty Runtime State

### Symptom

- strange relaunch behavior
- inconsistent simulation timing
- old processes surviving in the background

### Fix

- added `tools/clean_benchmark_runtime.sh`
- use it before reruns after interrupted sessions

### Lesson

A clean runtime reset is part of the workflow, not an afterthought.

## 4. Old CSV Schema After Inspection Upgrades

### Symptom

- `inspection_log.csv` existed but did not match the new severity-aware schema

### Root Cause

Earlier benchmark runs created a simpler CSV before the richer fields were added.

### Fix

- the inspection plugin now rotates legacy CSV files automatically
- creates `inspection_log_legacy_<timestamp>.csv`
- starts a fresh CSV with the expected header

### Lesson

Output schemas evolve. Migration handling matters even in a portfolio project.

## 5. Gazebo Fuel Dependency Broke Visual Verification

### Symptom

- `Unable to find or download file`
- Gazebo server died before simulation was usable
- Nav2 never received stable simulation data

### Root Cause

The benchmark world from Nav2 referenced Fuel-hosted models and some nested asset paths still required network resolution at launch time.

### Why This Was A Serious Problem

- visual verification became unreliable
- benchmark startup depended on external asset availability
- repeated retries were masking a real reproducibility issue

### Fix Applied

1. copied the benchmark models into the package under `worlds/benchmark_assets/`
2. patched model references to local paths
3. created `warehouse_offline.sdf`
4. updated the benchmark launch file to export local Gazebo resource paths

### Result

The advanced GUI run completed successfully and could be documented with screenshots and artifacts.

### Lesson

A flaky benchmark is not a benchmark. Reliability fixes are part of robotics engineering.

## 6. Last Inspection Could Arrive After The Round Action Result

### Symptom

- risk that the final checkpoint result might be missing from the round summary

### Root Cause

Navigation completion and inspection event publication were close in time but not perfectly synchronized.

### Fix

- add a short round-boundary sync delay before final summary publication

### Lesson

Distributed systems often fail at boundaries, not in the middle.

## 7. Mission Success Is Not The Same As Mission Acceptance

### Symptom

- Nav2 action can succeed while the operational result should still be considered unsafe

### Fix

- separate `action_result=SUCCEEDED` from mission decision
- use severity and capture health to choose `CONTINUE`, `RECOVERY_RETRY`, or `HOLD`

### Lesson

Navigation success and mission success are related, but not identical.

