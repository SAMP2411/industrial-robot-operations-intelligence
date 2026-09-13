# Current Run Visual Walkthrough

This file explains one real verified GUI benchmark run in the order it happened.

## Run Setup

- Scenario seed: `6262`
- Critical anomalies allowed: `false`
- Goal of this run: show routine patrol, anomaly detection, and targeted follow-up in one readable example
- Full log: [current_run.log](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/current_run.log)
- Dashboard snapshot: [latest_dashboard.html](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/latest_dashboard.html)
- Final report snapshot: [latest_report.json](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/latest_report.json)
- Campaign state snapshot: [latest_campaign_state.json](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/latest_campaign_state.json)

## What You Would See

### 1. Routine patrol starts

The robot begins a full 5-checkpoint patrol. In Gazebo and RViz, this looks like a normal patrol lap through the warehouse.

Relevant log lines:

```text
Round 1 heading to checkpoint 1/5: east_aisle
Round 1 heading to checkpoint 2/5: upper_right_turn
Round 1 heading to checkpoint 3/5: upper_left_turn
Round 1 heading to checkpoint 4/5: west_aisle
Round 1 heading to checkpoint 5/5: spawn_lane
```

### 2. The robot inspects at each stop

At each checkpoint, Nav2 reaches the goal and the inspection plugin captures and scores the asset.

Normal examples:

```text
Inspection saved at checkpoint east_aisle (index 0) -> asset=PMP-101 label=asset_nominal severity=normal health=100.0 confidence=0.70
Inspection saved at checkpoint upper_left_turn (index 2) -> asset=PNL-315 label=asset_nominal severity=normal health=100.0 confidence=0.70
```

### 3. Two warning anomalies are found

This run detected two warning-level issues during the routine patrol:

- `CMP-220` at `upper_right_turn` -> `belt_slip`
- `CNV-510` at `spawn_lane` -> `roller_imbalance`

Relevant log lines:

```text
Inspection saved at checkpoint upper_right_turn (index 1) -> asset=CMP-220 label=belt_slip severity=warning health=73.1 confidence=0.99
Inspection saved at checkpoint spawn_lane (index 4) -> asset=CNV-510 label=roller_imbalance severity=warning health=73.7 confidence=0.99
```

Evidence images from this exact run:

- [0001_upper_right_turn_belt_slip_11527650000000_annotated.png](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/0001_upper_right_turn_belt_slip_11527650000000_annotated.png)
- [0004_spawn_lane_roller_imbalance_11562948000000_annotated.png](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/0004_spawn_lane_roller_imbalance_11562948000000_annotated.png)

### 4. The mission layer makes a decision

After the routine lap, the robot does not blindly keep looping. It summarizes the round and decides what to do next.

In this run, the decision was `TARGETED_FOLLOW_UP`, meaning:

- routine patrol found suspicious assets
- the robot should re-check only those assets
- it should not waste time re-running the whole route immediately

Relevant log line:

```text
Round 1 summary: duration=62.073s ... anomalies=2 ... decision=TARGETED_FOLLOW_UP ... follow_up_assets=CMP-220|CNV-510 ...
```

### 5. The robot performs a short follow-up round

Now the patrol becomes selective. Instead of visiting all 5 checkpoints again, it only visits the 2 assets that need confirmation.

Relevant log lines:

```text
Starting targeted follow-up round 2 (follow-up pass 1) with 2 checkpoints across assets CMP-220, CNV-510.
Follow-up round 2 pass 1 heading to asset CMP-220 checkpoint 1/2: upper_right_turn
Follow-up round 2 pass 1 heading to asset CNV-510 checkpoint 2/2: spawn_lane
```

### 6. The findings are stable, so the system de-escalates

The follow-up pass sees the same warning findings again. Because they are stable and not critical, the mission does not loop forever. It resumes routine patrol and keeps those assets on a watchlist.

Relevant log line:

```text
Round 2 summary: duration=27.648s ... phase=targeted_follow_up ... anomalies=2 ... decision=RESUME_WATCHLIST ... reason=Follow-up assets remained stable across repeated passes. Resuming routine patrol while keeping them on the watchlist.
```

## Short Mental Model

Think of the system like this:

- Nav2 drives the robot to places
- the inspection plugin looks at the asset when the robot arrives
- the mission node decides whether the result means continue, hold, or re-check
- the report node writes operator-facing outputs

## Why This Run Is Useful

This single run shows the full advanced loop:

1. normal patrol
2. anomaly detection
3. round summary
4. targeted re-inspection
5. watchlist-based de-escalation

That makes it a good demo run for explaining the system in interviews.
