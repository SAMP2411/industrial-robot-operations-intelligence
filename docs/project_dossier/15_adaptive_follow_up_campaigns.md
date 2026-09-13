# Adaptive Follow-Up Campaigns

## Why This Phase Exists

The earlier system could detect and prioritize risky assets, but it still behaved like a simple patrol loop:

- do one round
- report findings
- start the next round

Real inspection products do more than that. They adapt the mission after new evidence appears. This phase adds that missing layer.

The design goal was:

- let a routine patrol discover problematic assets
- automatically launch a focused re-inspection pass on only those assets
- preserve campaign history across rounds
- do this without changing Nav2 itself

## What Was Added

### 1. Adaptive Mission Phase Switching

The patrol node now supports two route phases:

- `routine`
- `targeted_follow_up`

After a routine round, the mission node ranks inspection results and selects follow-up assets using severity, asset priority, health score, review state, and capture success.

If the safety policy does not require a hold, the node now launches a smaller Nav2 route containing only the selected assets.

Why this matters:

- the robot now behaves more like an inspection campaign manager than a waypoint loop
- it demonstrates system-level reasoning, not only navigation integration
- it gives you a strong interview story about separating motion from mission policy

### 2. Pose-Based Checkpoint Resolution

The waypoint inspection plugin used to assume:

- waypoint index in Nav2 route = checkpoint index in config

That is only safe for full-route patrols. It breaks when a follow-up route uses a subset of checkpoints.

The plugin now resolves the active checkpoint by pose, with a waypoint-index fallback.

Why this matters:

- subset follow-up routes inspect the correct physical asset
- the system no longer depends on brittle index ordering
- this is closer to how robotics systems should treat real-world tasks

### 3. Campaign History and Asset Timeline Artifacts

The reporting layer now writes:

- `asset_history.csv`
- `latest_campaign_state.json`
- `<run_id>/campaign_state.json`

These outputs preserve:

- round timeline
- selected assets per round
- follow-up assets per round
- per-asset latest condition
- per-asset inspection count
- whether an asset is still outstanding

Why this matters:

- the robot now has memory across rounds, not only one-round snapshots
- dashboards and external tools can reason about asset drift over time
- this looks much more like product telemetry than raw robotics debug logs

### 4. Scenario Control for Warning-Only Verification

The scenario generator now accepts `allow_critical`.

That makes it possible to intentionally verify automatic targeted follow-up behavior without the mission stopping immediately on a critical hold.

Why this matters:

- it improves testability
- it separates “policy test” from “perception test”
- it gives you deterministic reproduction of mission behaviors

## Files That Made This Phase Real

- `src/factory_inspection_mission/src/patrol_mission_node.cpp`
- `src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp`
- `src/factory_inspection_mission/include/factory_inspection_mission/inspection_at_waypoint.hpp`
- `src/factory_inspection_mission/src/mission_report_node.cpp`
- `src/factory_inspection_mission/launch/benchmark_scenario_generator.py`
- `src/factory_inspection_mission/launch/benchmark_patrol.launch.py`
- `src/factory_inspection_mission/launch/patrol_mission.launch.py`

## Verified Outcome

Verified on April 6, 2026 using:

```bash
FACTORY_SCENARIO_ALLOW_CRITICAL=false
FACTORY_SCENARIO_SEED=6262
FACTORY_SCENARIO_MIN_ANOMALIES=2
FACTORY_SCENARIO_MAX_ANOMALIES=2
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False
```

Observed behavior:

- Round 1 completed successfully
- Round 1 found two warning assets:
  - `CMP-220` -> `belt_slip`
  - `CNV-510` -> `roller_imbalance`
- Round 1 decision became `TARGETED_FOLLOW_UP`
- The next Nav2 goal contained only two checkpoints for:
  - `CMP-220`
  - `CNV-510`
- During follow-up round 2, waypoint index `0` correctly resolved to `upper_right_turn`, proving the new pose-based checkpoint matching worked
- The reporting layer wrote:
  - `latest_campaign_state.json`
  - `asset_history.csv`
  - `round_0002_report.*`

Key observed output:

> Round 1 summary: duration=82.407s, action_result=SUCCEEDED, ... decision=TARGETED_FOLLOW_UP, ... follow_up_assets=CMP-220|CNV-510

> Starting targeted follow-up round 2 (follow-up pass 1) with 2 checkpoints across assets CMP-220, CNV-510.

## Engineering Reasoning

### Why mission logic owns follow-up routing

Nav2 should own:

- path planning
- control
- waypoint execution

The mission layer should own:

- which assets matter next
- whether to hold, continue, retry, or rescan
- how inspection evidence changes the next route

That separation keeps the navigation stack reusable while allowing the product logic to become more sophisticated.

### Why pose matching was necessary

A full patrol route can get away with index-based matching.

A targeted follow-up route cannot.

If the route becomes:

- `[CMP-220, CNV-510]`

then waypoint `0` is no longer `east_aisle`.

Pose matching solved that correctly and cleanly.

## Interview Questions

1. Why should targeted follow-up be implemented in the mission node instead of inside Nav2?
2. Why does subset-route inspection require pose-based checkpoint matching?
3. What operational value does `asset_history.csv` provide that a one-round report does not?
4. Why is a warning-only scenario generator useful when testing an adaptive mission system?

## Honest Bottlenecks After This Phase

This phase made the system behavior more realistic, but it also exposed the next real limits:

- the follow-up loop can keep rediscovering the same unresolved warning assets because there is still no repair action, only re-inspection
- the mission does not yet reason about trend improvement or degradation; it only reasons about current status
- the inspection stack is still benchmark perception, not learned plant-grade perception
- the simulator is still the slowest and flakiest part of repeated verification

That means the next frontier is not “more looping.” It is:

- stronger perception
- better stop criteria for adaptive campaigns
- richer operator policy for unresolved-but-stable warnings
