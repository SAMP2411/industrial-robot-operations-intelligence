# Iteration Testing README

If you are new to this repo, start with [README.md](/home/samarth/projects/industrial-robot-operations-intelligence/docs/README.md) and then [PIPELINE_WORKFLOW_FOR_BEGINNERS.md](/home/samarth/projects/industrial-robot-operations-intelligence/docs/PIPELINE_WORKFLOW_FOR_BEGINNERS.md). They explain the full flow in simple language before you use this shorter maintenance checklist.

This is the shortest safe workflow to keep the project healthy while you iterate.

## Rule Zero

Do not run the benchmark with:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
export QT_OPENGL=software
```

On this machine those variables can crash Gazebo's sensor/render pipeline and leave Nav2 stuck in `inactive`.

## 1. Build After Code Changes

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select factory_inspection_interfaces factory_inspection_mission
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
```

## 2. Clean Old Runtime State

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
./tools/clean_benchmark_runtime.sh
```

Use this before every rerun if the previous benchmark was interrupted.

## 3. Fast Smoke Test After Each Iteration

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
./tools/run_iteration_smoke_test.sh
```

What this does:

- cleans the runtime
- uses a stable default seed
- runs the benchmark headless
- retries if startup flakes happen
- declares success once the robot has reached the cross-warehouse segment and is heading to `mid_east_service_bay`
- exits non-zero on failure
- prints the latest smoke-test log path instead of pretending a full round report was generated

Why this changed:

- the current advanced benchmark is longer than the original MVP
- waiting for a full `Round 1 summary:` was causing false failures even when the robot was already moving correctly
- the smoke test is now a fast health check, not a full-duration benchmark

## 4. Manual Headless Verification

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False
```

Success signs:

- `Entity creation successful.`
- `Managed nodes are active`
- `Nav2 accepted patrol round 1.`
- `Round 1 heading to checkpoint 1/10: spawn_lane`
- `Round 1 heading to checkpoint 6/10: mid_east_service_bay`

## 5. Full Round Verification

Use this when you want the complete round summary rather than the fast smoke check.

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False
```

Wait for:

- `Round 1 summary:`

## 6. Visual Verification

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=False use_rviz:=False
```

Optional RViz run:

```bash
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=False use_rviz:=True
```

## 7. If The Mission Waits Forever

Run:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /waypoint_follower
```

Healthy target:

- all four should be `active [3]`

If `waypoint_follower` is `inactive [2]`, the mission node is usually waiting correctly and Gazebo / TF / Nav2 activation is the real problem upstream.

## 8. Artifacts To Check After A Good Run

```bash
ls -lah ~/.ros/factory_inspection/benchmark
```

High-signal files after a full run:

- `inspection_log.csv`
- `latest_report.json`
- `latest_dashboard.html`
- `latest_campaign_state.json`
- `*_annotated.png`

High-signal files after a smoke test:

- latest `retry_logs/benchmark_attempt_*.log`
- newest `*_annotated.png`
- updated `inspection_log.csv`

## 9. Suggested Per-Iteration Rhythm

1. Make one focused change
2. Build
3. Run `./tools/run_iteration_smoke_test.sh`
4. If it passes, do one visual run
5. Check `latest_report.json`
6. Record what changed and what was verified

## 10. Multi-Platform Validation

Use these when you want to validate the same mission stack against different robot profiles.

`tb4` baseline:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False robot_profile:=tb4 robot_name:=scout_alpha
```

`spot_like` platform-adapter validation:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=True use_rviz:=False robot_profile:=spot_like robot_name:=spot_alpha
```

Current interpretation:

- `tb4` is the known-good regression baseline
- `spot_like` is the current adapter-validation profile
- `anymal_like` is still a tuning/debug target rather than a fully verified profile

## 11. Fleet Validation

Two-robot fleet launch:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_fleet.launch.py \
  headless:=True \
  use_rviz:=False \
  fleet_robots:='scout_alpha:tb4,response_beta:tb4'
```

Fleet artifacts land in:

```bash
ls -lah ~/.ros/factory_inspection/fleet
```

High-signal files:

- `fleet_manifest.json`
- `latest_fleet_state.json`
- `latest_fleet_dashboard.html`
- per-robot report folders under `~/.ros/factory_inspection/fleet/`

Current status:

- fleet launch, robot partitioning, and fleet supervisor startup are implemented
- full multi-robot Nav2 activation in one world is still under active debugging
