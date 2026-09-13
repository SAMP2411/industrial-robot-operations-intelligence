# Hardening And Regression

## Why This Phase Exists

After the adaptive follow-up phase, the project had become more capable but still had three practical reliability problems:

- stable warning assets could trigger repeated follow-up passes without adding new information
- benchmark startup still had intermittent Gazebo failures
- validation depended too much on manual reruns

This phase was about turning the system from “advanced demo” into “repeatable engineering benchmark.”

## Problems Found

### 1. Repeated Follow-Up With No New Information

The mission could correctly trigger targeted follow-up, but if the same warning assets stayed unchanged, the robot would keep revisiting them until the configured budget was exhausted.

That was technically bounded, but it was not smart.

### 2. Gazebo Startup Flake

Repeated regression attempts showed `gz sim` sometimes died immediately with:

- `Unable to find or download file`

Investigation showed the stock TB4 simulation launch from Nav2 was generating a temporary `/tmp/nav2_*.sdf` through `xacro` and launching Gazebo in a separate action. That made the temp world generation path vulnerable to launch-order races.

### 3. Weak Automation Around Verification

Even after the robot logic was improved, benchmarking still relied on:

- manual cleanup
- manual relaunch
- manual log inspection

That is not good enough once the project gets large.

## What Was Changed

### 1. Stable Watchlist Resume Policy

The mission node now compares follow-up assets against their last finalized inspection results.

If a targeted follow-up pass shows:

- same warning severity
- no meaningful health improvement
- no worsening

then the mission now switches to:

- `RESUME_WATCHLIST`

instead of launching another identical targeted follow-up pass.

Why this matters:

- the robot now distinguishes unresolved-but-stable assets from actively changing assets
- mission time is not wasted on identical rescans
- the project demonstrates better operational judgment

### 2. Deterministic Local TB4 Benchmark Sim Launch

A local launch file was added:

- `launch/benchmark_tb4_local_sim.launch.py`

This launch path:

- launches `gz sim` directly on the generated world SDF
- keeps the TB4 spawn, Nav2 bringup, and RViz flow
- removes the temp-world xacro race from the stock launch path

Why this matters:

- startup is more deterministic
- the benchmark is now less dependent on hidden launch timing
- the previous `Unable to find or download file` failure path was dramatically reduced

### 3. Stronger Benchmark Cleanup And Retry Tooling

The tool layer now includes:

- `tools/clean_benchmark_runtime.sh`
- `tools/run_benchmark_with_retry.sh`
- `tools/run_benchmark_regression.sh`

Why this matters:

- stale Gazebo / Nav2 processes are cleaned more reliably
- the benchmark can auto-retry cleanly when startup fails
- repeated seed-based checks are now scriptable instead of manual

### 4. Safer Nav2 Benchmark Tuning

The benchmark params were tuned conservatively:

- MPPI trajectory visualization disabled
- MPPI batch size reduced
- planner expected frequency relaxed

An attempted over-aggressive slowdown of the controller caused `Resulting plan has 0 poses in it`, so that change was rolled back.

Why this matters:

- this phase did not just add changes
- it included finding one bad tuning idea, proving it was harmful, and backing it out

## Files Changed In This Phase

- `src/factory_inspection_mission/src/patrol_mission_node.cpp`
- `src/factory_inspection_mission/config/warehouse_benchmark_nav2_params.yaml`
- `src/factory_inspection_mission/launch/benchmark_tb4_local_sim.launch.py`
- `src/factory_inspection_mission/launch/benchmark_patrol.launch.py`
- `src/factory_inspection_mission/launch/patrol_mission.launch.py`
- `tools/clean_benchmark_runtime.sh`
- `tools/run_benchmark_with_retry.sh`
- `tools/run_benchmark_regression.sh`

## Verified Outcome

### Stable Follow-Up Policy

Verified on April 6, 2026 with seed `6262`:

- round 1 detected warning assets `CMP-220` and `CNV-510`
- round 2 re-inspected those assets
- round 2 ended with:
  - `mission_decision=RESUME_WATCHLIST`

Observed result:

> Round 2 summary: duration=35.85s, action_result=SUCCEEDED, ... decision=RESUME_WATCHLIST, ... reason=Follow-up assets remained stable across repeated passes. Resuming routine patrol while keeping them on the watchlist.

### Startup Hardening

Verified after the local sim launch swap:

- seed `4242` succeeded on attempt 1
- seed `5151` succeeded on attempt 1

Both were run through:

- `tools/run_benchmark_with_retry.sh`

This is important because the same `4242` seed had previously failed twice in a row with Gazebo startup errors.

## Honest Remaining Limits

This hardening pass removed the main avoidable runtime issues, but it did not make the project magically “finished.”

The remaining meaningful limits are now:

- perception still depends on heuristic benchmark logic plus simulated channels
- watchlist assets resume to routine patrol, but there is still no operator acknowledgement loop or maintenance ticket lifecycle
- broader long-run regression across many seeds and many hours has not been exhausted yet

That is a much better place to be:

- the remaining limits are now product-depth limits
- not fragile launch or mission-control bugs
