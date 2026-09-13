# Autonomous Factory Inspection Robot Manual

## Concepts

### Mission Layer vs Navigation Layer
- The mission layer decides *what happens next*.
- Nav2 decides *how the robot physically gets there*.
- Our `Option A` design keeps looping logic in the mission layer, so one Nav2 goal equals one patrol round.

### Action Client
- An action is for long-running work that needs feedback while it runs.
- Our mission node is an action client to Nav2's `/follow_waypoints` server.
- Why it exists here: patrol is not instant, and we want waypoint progress plus a final round result.

### Benchmark-First Workflow
- First prove the mission loop in a stock Nav2 simulation.
- Then freeze the mission interface and move to a custom factory environment.
- Why it exists: when navigation, world modeling, and mission logic all change together, debugging becomes blurry.

### Waypoint Task Executor Plugin
- A Nav2 waypoint task executor plugin runs *after arrival at a waypoint*.
- It fits between navigation and inspection: Nav2 gets the robot to the checkpoint, then the plugin does the checkpoint-local work.
- Why it exists here: we want `stop -> capture -> classify -> save -> continue` without forking a second mission state machine.

### RViz MarkerArray
- `visualization_msgs/MarkerArray` is the lightweight way to put semantic state into RViz.
- It fits in the logging and operator-awareness layer: CSV is for reports, saved images are for evidence, markers are for live situational awareness.
- Why it exists here: an anomaly should be visible on the map the moment it is detected, not only after opening a log file.

### Event-Driven Reporting
- A good robotics system should publish structured facts while it runs, not force later tools to scrape terminal text.
- We now publish inspection events and round summary events as ROS topics, then a separate reporter node writes round reports from those events.
- Why it exists here: it turns the project from a demo with logs into a system with stable interfaces.

### Severity-Aware Inspection
- A real inspection robot needs more than a boolean anomaly flag.
- We now classify each checkpoint as `normal`, `warning`, or `critical`, and each result carries a recommended operator action.
- Why it exists here: a `warning` should not trigger the same response as a `critical` alarm, even if both are anomalies.

### Round-Boundary Synchronization
- Nav2 finishes waypoint execution first, but inspection events can arrive a few milliseconds later.
- The mission node now waits briefly before publishing the round summary so it can make a decision using complete inspection data.
- Why it exists here: otherwise the last checkpoint can be missing from the safety decision and the round report.

### Mission Safety Policy
- The mission node now decides whether to `CONTINUE`, `RECOVERY_RETRY`, or `HOLD` after every round.
- That decision uses Nav2 outcome plus inspection severity and capture health.
- Why it exists here: a hireable robotics project should show that navigation and perception affect operations policy, not just logs.

### Static Dashboard Artifact
- The reporter now writes a standalone HTML dashboard in addition to JSON and Markdown.
- It fits in the productization layer: operators can open one file and immediately see evidence, severity, and mission decision.
- Why it exists here: it turns structured telemetry into something a teammate or hiring manager can scan quickly.

### Asset-Centric Inspection
- The project no longer thinks only in waypoint names; it now tracks `asset_id`, display name, type, zone, priority, and enabled modalities.
- It fits between mission config and reporting: the same inspection event can now drive mission decisions, dashboards, and interview explanations in business terms.
- Why it exists here: commercial inspection products are asset-centric, not waypoint-centric.

### Multimodal Inspection Fusion
- Each inspection result now carries visual, thermal, acoustic, and gas-style evidence channels when those modalities are enabled for an asset.
- It fits inside the waypoint plugin: navigation gets the robot to the point of interest, and the plugin fuses sensor evidence into one health assessment.
- Why it exists here: industrial inspection systems are more useful when one asset assessment combines multiple signals instead of treating every anomaly as a single camera label.

### Targeted Follow-Up Mission Profile
- The benchmark can now run a smaller `targeted_follow_up` mission by selecting only specific assets through `FACTORY_TARGET_ASSETS`.
- It fits above the mission loop: the route is generated from the selected asset list, then the same mission/report stack executes it.
- Why it exists here: it mirrors the site-centric “inspect these assets now” workflow used by modern industrial inspection platforms.

### Run Identity
- Reports now use a unique `run_id` in addition to `scenario_id`.
- It fits in the event layer and reporting layer: inspection events and round summaries from different launches can no longer be merged accidentally just because they share `round_number=1`.
- Why it exists here: repeated simulation benchmarks are common during development, and report integrity matters.

## Current Workflow

1. If a previous benchmark run was interrupted, clean the runtime with `tools/clean_benchmark_runtime.sh`.
2. Run the benchmark launch that starts the stock warehouse simulation, Nav2, and the patrol mission node together.
3. Watch for one clean patrol round summary with no missed waypoints.
4. Only after that benchmark is stable, move on to the custom factory floor and inspection stops.
5. For the inspection MVP, inspect the artifact folder and CSV after one round to confirm evidence was saved at each checkpoint.
6. For the advanced reporting layer, confirm that `round_0001_report.json`, `round_0001_report.md`, and `latest_dashboard.html` appear after the first completed patrol round.
7. In the current benchmark profile, expect the mission to enter `HOLD` after round 1 because the benchmark includes a controlled critical anomaly.
8. To run a targeted follow-up mission instead of the full route, set `FACTORY_TARGET_ASSETS`, for example `FACTORY_TARGET_ASSETS='CMP-220,PNL-315'`.

### Benchmark Exit Criteria
- `/follow_waypoints` becomes available.
- Nav2 accepts the round goal.
- The robot visits each benchmark checkpoint once.
- The mission node prints a `SUCCESS` round summary with severity counts.
- The mission decision is `HOLD` because the benchmark includes one critical checkpoint.

### Current Benchmark Command
- `source /opt/ros/jazzy/setup.bash`
- `source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash`
- `ros2 launch factory_inspection_mission benchmark_patrol.launch.py`

### Visual Benchmark Command
- `source /opt/ros/jazzy/setup.bash`
- `source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash`
- `ros2 launch factory_inspection_mission benchmark_patrol.launch.py use_rviz:=True headless:=False`
- The benchmark RViz profile now includes an `InspectionMarkers` display on `/inspection_markers`.
- The benchmark launch now uses a local offline warehouse world and local Gazebo resource paths so visual verification does not depend on Fuel downloads at launch time.

### Inspection Artifacts
- Saved under `~/.ros/factory_inspection/benchmark`
- Images are named with waypoint index, checkpoint name, inspection label, and timestamp.
- `inspection_log.csv` now records round number, severity, recommended action, anomaly flag, pose, capture status, and saved image path.
- RViz anomaly markers are published on `/inspection_markers` and persist for late subscribers using transient-local QoS.
- `round_0001_report.json` is the machine-readable round report.
- `round_0001_report.md` is the human-readable round report.
- `round_0001_report.html` and `latest_dashboard.html` are operator-facing dashboard artifacts with evidence thumbnails.
- `latest_report.json` and `latest_report.md` mirror the most recently completed round.

### What You Should See
- Gazebo GUI with the TurtleBot4 moving through the warehouse route.
- RViz showing the map, robot, costmaps, and Nav2 state while the patrol is running.
- Terminal output stepping through checkpoint names and printing a round summary at completion.

### Benchmark Result
- On April 5, 2026, the warehouse benchmark completed one full patrol round successfully.
- Observed result: `Round 1 summary: duration=47.361s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], status=SUCCESS`
- The node then paused for 3 seconds and started round 2, which confirms the Option A resend-per-round loop works end to end.
- On April 5, 2026, the event-driven reporting layer also completed successfully.
- Observed report result: `Wrote round 1 report with 5 inspections and 1 anomalies -> /home/samarth/.ros/factory_inspection/benchmark/round_0001_report.json`
- On April 5, 2026, the next-level benchmark profile added severity-aware inspection and safety policy successfully.
- Observed advanced result: `Round 1 summary: duration=46.398s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`
- The reporter generated `round_0001_report.json`, `round_0001_report.md`, and `latest_dashboard.html` for that same run.
- On April 5, 2026, the advanced visual benchmark was re-verified after fixing the Gazebo world dependency by using local benchmark assets.
- Observed visual result: `Round 1 summary: duration=44.844s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`
- The visual run also saved checkpoint evidence for `upper_right_turn` as `gauge_high_alarm` and `upper_left_turn` as `needle_drift`.

## Interview Answers

### Why resend the waypoint list after each round instead of repeating it upfront?
- It keeps round boundaries explicit.
- It makes summaries, stop conditions, and future inspection hooks easier to add.
- It separates mission orchestration from Nav2's internal waypoint execution.

### Why use a stock benchmark world before building the custom factory map?
- It reduces the number of moving parts during early debugging.
- It lets us validate mission logic and Nav2 integration against a known-good environment.
- It creates a concrete benchmark gate before adding project-specific complexity.

### Why put checkpoint inspection inside Nav2's waypoint task executor instead of the mission node?
- Arrival is a Nav2 concern, so the most reliable place to trigger checkpoint-local work is exactly where Nav2 marks a waypoint as reached.
- It preserves clean ownership: mission node owns laps and summaries, Nav2 owns motion and per-waypoint hooks.
- It scales better when we later replace the controlled classifier with a real vision model.

### Why publish structured ROS events instead of parsing terminal logs later?
- Logs are for humans; topics are for systems.
- Topics give us a stable contract for dashboards, reports, tests, and future monitoring nodes.
- It keeps reporting logic separate from navigation and inspection execution.

### Why delay the round summary instead of publishing it the instant Nav2 finishes?
- Nav2 knows the route is done, but the last inspection result may still be in flight.
- The short delay gives the mission node a complete round picture before it makes a safety decision.
- It avoids race conditions between navigation completion and inspection telemetry.

### Why hold after a critical anomaly instead of immediately starting round 2?
- Because patrol is not the only system objective; safe response matters too.
- A critical checkpoint means the next useful action may be operator review, not another lap.
- It demonstrates that the mission layer can turn perception into operations policy.

## Errors and Fixes

### No `/follow_waypoints` action server
- Symptom: mission node keeps printing that it is waiting for Nav2.
- Checks:
  - Did Nav2 launch successfully?
  - Is the action name `/follow_waypoints` available?
  - Are localization and map topics healthy enough for Nav2 to activate?

### Stale benchmark processes after an interrupted run
- Symptom: repeated `TF_OLD_DATA`, inconsistent sim timestamps, random Nav2 instability, or behavior that gets worse on each rerun.
- Cause: old `gz sim` and Nav2 processes can survive a timed or interrupted launch.
- Fix: run `tools/clean_benchmark_runtime.sh`, then relaunch the benchmark from a clean slate.

### Benign visualization warnings
- RViz may print some startup shader or message-filter warnings while displays initialize.
- Gazebo may print Qt or EGL warnings even when the GUI still works.
- Treat those as secondary unless the windows close or the patrol stops progressing.

### No inspection images saved
- Symptom: patrol succeeds but `inspection_log.csv` shows `capture_ok=false` or image paths are empty.
- Checks:
  - Is `/rgbd_camera/image` publishing in the benchmark sim?
  - Did the waypoint follower load `factory_inspection_mission::InspectionAtWaypoint`?
  - Is the save directory writable?

### No anomaly marker visible in RViz
- Symptom: the anomaly is in the CSV, but nothing appears on the map.
- Checks:
  - Is RViz using the benchmark config with the `InspectionMarkers` display?
  - Does `/inspection_markers` have a publisher and at least one marker message?
  - Is the marker display using `map` as the fixed frame and `Transient Local` durability?

### Visual benchmark fails with Fuel download errors
- Symptom: Gazebo logs `Unable to find or download file` before simulation comes up.
- Cause: the stock world referenced remote Fuel assets at launch time.
- Fix: the benchmark now ships an offline world and local asset folder under `factory_inspection_mission/worlds/`, so relaunch using the project benchmark launch after rebuilding.

### No round report file appears
- Symptom: patrol succeeds, but there is no `round_0001_report.json`.
- Checks:
  - Did `mission_report_node` start successfully?
  - Are `/inspection_results` and `/patrol_round_summaries` both being published?
  - Is the report directory writable?
  - Did the run stop before the first round fully completed?

### Legacy CSV schema after inspection upgrade
- Symptom: `inspection_log.csv` exists, but the header does not match the new severity-aware fields.
- Cause: a previous benchmark run created the old CSV schema before the inspection upgrade.
- Fix: the plugin now rotates the old file to `inspection_log_legacy_<timestamp>.csv` and starts a fresh CSV automatically.

### Report file mixes checkpoints from multiple reruns
- Symptom: `round_0001_report.json` shows more checkpoint entries than the round summary printed in the terminal.
- Cause: earlier versions keyed reports only by round number, which is not unique across repeated launches.
- Fix: report events now carry a unique `run_id`, and the reporter groups data by `run_id + round_number` instead of just `round_number`.

### Advanced randomized benchmark status
- Symptom: the robot completes the patrol, but inspection accuracy is poor even though the saved images and reports look structurally correct.
- Current verified state on April 5, 2026:
  - Random scenario generation works.
  - Asset-centric mission config works.
  - Multimodal inspection fusion works.
  - Review-queue policy now demotes weak visual-only findings on assets that should have corroborating modalities.
  - The inspection plugin now saves both raw and annotated evidence images.
  - The report node now writes run-scoped artifacts under `~/.ros/factory_inspection/benchmark/<run_id>/`.
  - The report node now publishes a lightweight machine-readable `latest_dashboard_state.json`.
  - A fixed-seed benchmark (`FACTORY_SCENARIO_SEED=4242`) completed one full round with `action_result=SUCCEEDED`, `accuracy=100%`, `false_positive_count=0`, and the conveyor false positive converted into `review_required=true`.
  - A second randomized seed (`FACTORY_SCENARIO_SEED=5151`) also completed with `accuracy=100%`, `false_positive_count=0`, and the same review-queue behavior on the weak conveyor visual hit.
- Practical takeaway:
  - The mission architecture is now much closer to an industrial product architecture.
  - The current stack is strong for a portfolio benchmark: the robot patrols, fuses inspection channels, scores confidence, preserves audit trails, and distinguishes true anomalies from review-only findings.
  - The next real bottleneck is broader multi-seed validation and stronger real perception models, not Nav2, mission policy, or reporting.

### Adaptive follow-up campaign status
- Verified on April 6, 2026 with:
  - `FACTORY_SCENARIO_ALLOW_CRITICAL=false`
  - `FACTORY_SCENARIO_SEED=6262`
  - `FACTORY_SCENARIO_MIN_ANOMALIES=2`
  - `FACTORY_SCENARIO_MAX_ANOMALIES=2`
- Current verified behavior:
  - Round 1 completes as a full routine patrol.
  - Warning assets are ranked into `follow_up_assets`.
  - The mission node automatically launches a second Nav2 goal containing only the selected follow-up assets.
  - The inspection plugin now matches checkpoints by pose, so subset routes still inspect the correct asset.
  - The report node now writes `latest_campaign_state.json` and append-only `asset_history.csv`.
- Practical takeaway:
  - The robot now behaves like a small inspection campaign manager, not only a patrol loop.
  - Unresolved warning assets can be revisited immediately without re-running the entire route.

### Follow-up rounds keep revisiting the same assets
- Symptom: the robot completes a targeted follow-up pass, then launches another focused pass on the same assets.
- Cause: the mission now correctly keeps chasing unresolved findings, but there is still no “repair completed” or “stability accepted” policy.
- Updated behavior:
  - if warning assets remain stable across repeated follow-up passes, the mission can now switch to `RESUME_WATCHLIST`
  - this keeps the assets on the watchlist while resuming routine patrol
- Interpretation:
  - this is now a product-policy bottleneck, not a Nav2 bottleneck
  - the next improvement should be a smarter stop rule based on trend stability, confidence, or operator acknowledgement

### Follow-up route inspects the wrong checkpoint
- Symptom: a targeted follow-up route visits only two waypoints, but inspection logs show the wrong checkpoint names.
- Cause: older logic assumed `waypoint_index == checkpoint_index`.
- Fix:
  - the inspection waypoint plugin now selects checkpoints by pose with index fallback
  - verified during the April 6, 2026 follow-up campaign run where follow-up round waypoint `0` correctly mapped to `upper_right_turn`

### Gazebo benchmark startup fails immediately
- Symptom: launch stops early with `Unable to find or download file` before the robot begins moving.
- Root cause found:
  - the stock TB4 simulation launch generated a temporary `/tmp/nav2_*.sdf` through `xacro`
  - Gazebo and the temp-world generation path could race during launch
- Fix:
  - the benchmark now uses a local sim launch that starts `gz sim` directly on the already-generated world SDF
  - verified with previously flaky seeds `4242` and `5151`, both succeeding on attempt 1 after the fix

### Cleanup script leaves stale sim processes behind
- Symptom: old `gz sim` or Nav2 processes survive after interrupted runs.
- Cause: the older cleanup script used a single giant regex pattern, which proved less reliable in practice than expected.
- Fix:
  - cleanup now issues separate `pkill` passes, then a forced `pkill -9` pass
  - this is more predictable and easier to debug

## Debugging Steps

1. Confirm the checkpoint YAML loads and prints all checkpoint names at startup.
2. Confirm Nav2 exposes `/follow_waypoints`.
3. Confirm the robot reaches one full patrol round before worrying about inspection logic.
4. Confirm the round report files match the anomaly count, severity counts, and evidence paths from the inspection outputs.
5. Confirm the mission decision matches the configured safety policy, for example `HOLD` after a controlled critical anomaly.
6. If you repeat the same seed several times, confirm the latest report has the expected `run_id` and that `inspection_count` matches the number of checkpoint entries in the JSON.
7. For adaptive campaigns, confirm `selected_assets` changes between the routine round and the targeted follow-up round.
8. For subset routes, confirm the checkpoint names in the inspection log still match the intended physical asset, not only the local waypoint index.
9. If startup is flaky, run `tools/run_benchmark_with_retry.sh` instead of doing repeated manual relaunches.
10. When benchmarking reliability, use fixed seeds and keep the retry log path so you can compare failures against successful runs.
