# Verification Log

This file records what was actually verified, not just what was intended.

## Verification Philosophy

- Build something small
- Run it
- Observe it
- Save evidence
- Record exact outcomes

## Phase 1 Verification

### Checkpoint: Mission Node Boot

Verified:

- package built successfully
- mission node loaded checkpoint YAML
- node waited for `/follow_waypoints` instead of crashing

Why it mattered:

- proved config loading
- proved the action client setup was sound

## Phase 1 Benchmark Verification

Verified:

- one full waypoint round completed in the benchmark world
- round boundary was detected in the mission node
- the node paused after the summary
- the round could be resent

Observed result from earlier benchmark runs:

- `Round 1 summary: duration=47.361s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], status=SUCCESS`

## Phase 2 Verification

Verified:

- 5 inspection images saved
- checkpoint metadata mapped correctly from YAML
- `upper_right_turn` produced the controlled anomaly
- CSV rows were written
- patrol still completed the round

Evidence:

- saved PNG per checkpoint under `~/.ros/factory_inspection/benchmark/`
- `inspection_log.csv`

## Phase 3 Verification

Verified:

- RViz markers appeared for anomalous checkpoints
- structured inspection events were published
- round summaries were published
- reporter node wrote JSON and Markdown files
- HTML dashboard was generated

Observed report output from earlier advanced runs:

- `Wrote round 1 report with 5 inspections and 1 anomalies`

## Phase 4 Verification

### Severity And Policy

Verified:

- warning and critical severity levels were propagated through the system
- the round summary contained warning and critical counts
- the mission decision became `HOLD` for the benchmark critical checkpoint

Observed output:

- `Round 1 summary: duration=46.398s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`

## Reliability Verification: Offline World Fix

### Failure Before The Fix

Observed symptom:

- Gazebo server died at launch with `Unable to find or download file`

Impact:

- missing `odom`
- Nav2 stayed inactive
- visual benchmark was not dependable

### Fix Applied

- benchmark models copied locally into the package
- local offline world created
- benchmark launch updated to use local resource paths

### Verification After The Fix

Date:

- April 5, 2026

Visual run verified:

- Gazebo GUI launched
- RViz launched
- Nav2 activated
- robot completed round 1
- critical checkpoint image saved
- warning checkpoint image saved
- final mission decision was `HOLD`

Observed output:

- `Inspection saved at checkpoint upper_right_turn (index 1) -> label=gauge_high_alarm severity=critical`
- `Inspection saved at checkpoint upper_left_turn (index 2) -> label=needle_drift severity=warning`
- `Round 1 summary: duration=44.844s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`
- `Mission placed in HOLD after round 1. Reason: A critical inspection result triggered the safety hold policy.`

## Artifacts Copied Into This Dossier

- `assets/visuals/rviz_hold_round1.png`
- `assets/visuals/gazebo_hold_round1.png`
- `assets/evidence/critical_upper_right_turn.png`
- `assets/evidence/warning_upper_left_turn.png`
- `assets/results/round_0001_report.json`
- `assets/results/round_0001_report.md`
- `assets/results/round_0001_report.html`
- `assets/results/latest_dashboard.html`
- `assets/results/inspection_log.csv`

## Acceptance State As Of April 5, 2026

Accepted as working:

- patrol mission loop
- inspection at checkpoint arrival
- saved evidence
- severity-aware results
- RViz marker output
- event-driven reporting
- HTML dashboard artifact
- mission hold policy
- offline visual benchmark run

## Adaptive Campaign Verification

### Purpose

Verify that the robot can:

- finish a routine patrol round
- select risky assets automatically
- launch a targeted follow-up round without manual retargeting
- preserve campaign history across rounds

### Configuration

Date:

- April 6, 2026

Run setup:

- `FACTORY_SCENARIO_ALLOW_CRITICAL=false`
- `FACTORY_SCENARIO_SEED=6262`
- `FACTORY_SCENARIO_MIN_ANOMALIES=2`
- `FACTORY_SCENARIO_MAX_ANOMALIES=2`
- `ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False`

### Verified Outcome

Verified:

- round 1 completed as a routine patrol with 5 checkpoints
- the mission selected `CMP-220` and `CNV-510` as follow-up assets
- round 2 launched automatically with only 2 checkpoints
- follow-up waypoint `0` correctly mapped to `upper_right_turn`, proving pose-based checkpoint matching worked
- the reporter wrote:
  - `latest_campaign_state.json`
  - `asset_history.csv`
  - `round_0002_report.json`

Observed output:

- `Round 1 summary: duration=82.407s, action_result=SUCCEEDED, nav2_error_code=0, phase=routine, selected_assets=PMP-101|CMP-220|PNL-315|VLV-410|CNV-510, missed=[], inspections=5, anomalies=2, warnings=2, critical=0, review_required=0, degraded_assets=2, thermal_alerts=0, acoustic_alerts=2, gas_alerts=0, capture_failures=0, decision=TARGETED_FOLLOW_UP, avg_health=89.3683, avg_confidence=0.816, lowest_health=73.0945, follow_up_assets=CMP-220|CNV-510, reason=Routine patrol detected assets that require a targeted follow-up inspection pass., status=SUCCESS`
- `Starting targeted follow-up round 2 (follow-up pass 1) with 2 checkpoints across assets CMP-220, CNV-510.`
- `Inspection saved at checkpoint upper_right_turn (index 0) -> asset=CMP-220 label=belt_slip severity=warning ...`
- `Inspection saved at checkpoint spawn_lane (index 1) -> asset=CNV-510 label=roller_imbalance severity=warning ...`
- `Round 2 summary: duration=37.011s, action_result=SUCCEEDED, nav2_error_code=0, phase=targeted_follow_up, selected_assets=CMP-220|CNV-510, missed=[], inspections=2, anomalies=2, warnings=2, critical=0, review_required=0, degraded_assets=2, thermal_alerts=0, acoustic_alerts=2, gas_alerts=0, capture_failures=0, decision=TARGETED_FOLLOW_UP, avg_health=73.4207, avg_confidence=0.855, lowest_health=73.0945, follow_up_assets=CMP-220|CNV-510, reason=Follow-up assets still require attention after the latest targeted inspection pass., status=SUCCESS`

### Artifacts Copied Into This Dossier

- `assets/results/latest_campaign_state.json`
- `assets/results/asset_history.csv`
- `assets/results/round_0002_report.json`
- `assets/results/round_0002_report.md`
- `assets/results/round_0002_report.html`

## Acceptance State As Of April 6, 2026

Accepted as working:

- adaptive targeted follow-up routing
- pose-safe subset checkpoint inspection
- campaign timeline artifact generation
- append-only asset history export
- automatic asset rescan after a warning-only routine round

## Hardening Verification

### Stable Watchlist Resume

Date:

- April 6, 2026

Configuration:

- `FACTORY_SCENARIO_ALLOW_CRITICAL=false`
- `FACTORY_SCENARIO_SEED=6262`
- success pattern set to `Round 2 summary:`

Verified:

- round 1 triggered a targeted follow-up
- round 2 re-inspected the same warning assets
- the mission no longer launched another identical follow-up pass
- round 2 decision became `RESUME_WATCHLIST`

Observed output:

- `Round 2 summary: duration=35.85s, action_result=SUCCEEDED, nav2_error_code=0, phase=targeted_follow_up, selected_assets=CMP-220|CNV-510, missed=[], inspections=2, anomalies=2, warnings=2, critical=0, review_required=0, degraded_assets=2, thermal_alerts=0, acoustic_alerts=2, gas_alerts=0, capture_failures=0, decision=RESUME_WATCHLIST, avg_health=73.4207, avg_confidence=0.855, lowest_health=73.0945, follow_up_assets=CMP-220|CNV-510, reason=Follow-up assets remained stable across repeated passes. Resuming routine patrol while keeping them on the watchlist., status=SUCCESS`

### Gazebo Startup Race Fix

Problem before the fix:

- seed `4242` failed twice in a row with `Unable to find or download file`
- the retry runner correctly caught the failure, but the underlying startup path was still flaky

Fix applied:

- replaced the stock TB4 benchmark launch path with a local sim launch that starts `gz sim` directly on the generated world SDF

Post-fix verification:

- seed `4242` succeeded on attempt 1
- seed `5151` succeeded on attempt 1

Observed runner output:

- `Benchmark succeeded on attempt 1. Log: /home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260406_011931_1.log`
- `Benchmark succeeded on attempt 1. Log: /home/samarth/.ros/factory_inspection/benchmark/retry_logs/benchmark_attempt_20260406_012053_1.log`

### Tooling Verification

Verified:

- `tools/run_benchmark_with_retry.sh` now catches:
  - Gazebo startup failure
  - Nav2 bringup failure
  - mission hold / mission round failure
- `tools/clean_benchmark_runtime.sh` now removes stale Gazebo and Nav2 processes more reliably than the old single-regex cleanup script
