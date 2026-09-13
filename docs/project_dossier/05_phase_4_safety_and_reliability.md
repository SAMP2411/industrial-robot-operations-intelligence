# Phase 4 Safety And Reliability

## Goal

Raise the project from a capable demo to a more realistic robotics system by adding policy, severity, and reproducibility improvements.

## Major Upgrades

- severity-aware inspection
- recommended operator actions
- round-boundary synchronization delay
- mission decision policy
- visual benchmark reliability fix with local world assets

## Severity Upgrade

The inspection result is no longer just anomaly or not anomaly.

The benchmark now uses:

- `normal`
- `warning`
- `critical`

This matters because the mission should not react the same way to all non-normal states.

## Recommended Action Upgrade

Each checkpoint result now includes an operator action such as:

- `continue_patrol`
- `schedule_recheck`
- `dispatch_operator_immediately`

This moves the project closer to operations-oriented robotics instead of just perception labeling.

## Round-Boundary Synchronization

Problem:

- Nav2 can finish the waypoint action slightly before the last inspection result arrives.

Fix:

- the mission node waits briefly before finalizing the round summary

Why that matters:

- the round summary must include the final checkpoint
- the policy decision must be made with complete inspection data

## Mission Policy Upgrade

The mission node now decides one of:

- `CONTINUE`
- `RECOVERY_RETRY`
- `HOLD`

Examples:

- If results are normal and the round succeeded, continue.
- If there is a retry-worthy issue, pause and retry.
- If a critical alarm occurs, hold the mission and surface the reason.

## Current Benchmark Policy Result

The benchmark intentionally contains:

- one critical checkpoint
- one warning checkpoint

That means the expected round-level outcome is:

- round succeeds from Nav2’s perspective
- mission still enters `HOLD` because operations policy overrides automatic continuation

This is exactly the kind of layered behavior worth discussing in interviews.

## Reliability Upgrade: Offline Benchmark World

### Problem Faced

The visual benchmark depended on Gazebo Fuel URLs at launch time. That caused repeated failures such as:

- `Unable to find or download file`
- missing `odom`
- Nav2 never fully activating

### Engineering Fix

The benchmark world was made local and reproducible by:

- vendoring the benchmark models under `src/factory_inspection_mission/worlds/benchmark_assets/`
- creating `warehouse_offline.sdf`
- updating the benchmark launch file to set local Gazebo resource paths

### Why This Was Important

- visual verification became trustworthy
- benchmark startup became reproducible
- the project now documents a real robotics reliability fix instead of hiding it

## Visual Verification After The Fix

On April 5, 2026, the advanced GUI benchmark was re-run after the local-world change.

Verified outcomes:

- Gazebo GUI launched and stayed alive
- RViz launched with the benchmark configuration
- Nav2 activated successfully
- the robot completed round 1
- the critical inspection at `upper_right_turn` was saved
- the warning inspection at `upper_left_turn` was saved
- the round ended with `decision=HOLD`

Observed final result:

- `Round 1 summary: duration=44.844s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`

## Why This Phase Is The “Next Level” Phase

This is the phase where the project stops being “a robot that patrols” and becomes “a system that makes operational decisions from structured robot outputs”.

## Interview Questions For Phase 4

### Why does the mission node own the `HOLD` decision instead of the waypoint plugin?

- Because `HOLD` is a round-level mission policy, not a per-checkpoint implementation detail.
- Because the mission node sees both Nav2 outcome and inspection summary.
- Because the plugin should report facts, not own fleet policy.

### Why did you fix the world dependency instead of simply retrying launches forever?

- Because reproducibility is part of engineering quality.
- Because a benchmark is only useful if it is dependable.
- Because reliability fixes are a strong portfolio story in robotics.

