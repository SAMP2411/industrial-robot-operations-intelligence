# Complete Workflow

## Purpose

This is the full manual workflow for building, running, verifying, and extending the project.

## Daily Development Loop

1. Build
2. Run one benchmark slice
3. Observe
4. Inspect only the relevant code
5. Record results
6. Make the next small improvement

## Environment Setup

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
```

## Build Workflow

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select factory_inspection_interfaces factory_inspection_mission
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
```

## Clean Runtime Before Relaunch

Use this when a previous benchmark was interrupted:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
./tools/clean_benchmark_runtime.sh
```

## Headless Benchmark Run

Use this for fast functional verification:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
ros2 launch factory_inspection_mission benchmark_patrol.launch.py
```

## Visual Benchmark Run

Use this when verifying Gazebo and RViz behavior:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
ros2 launch factory_inspection_mission benchmark_patrol.launch.py use_rviz:=True headless:=False
```

## What To Watch During A Run

- Nav2 lifecycle activation
- mission node round start
- checkpoint progress
- inspection save logs
- RViz markers
- final round summary
- report node write confirmation

## Expected Advanced Benchmark Behavior

Round 1 should:

- visit 5 checkpoints
- save 5 images
- record 1 critical result
- record 1 warning result
- generate reports
- finish with `decision=HOLD`

## Post-Run Artifact Check

Inspect:

```bash
ls -lah ~/.ros/factory_inspection/benchmark
```

Expected files include:

- `inspection_log.csv`
- `round_0001_report.json`
- `round_0001_report.md`
- `round_0001_report.html`
- `latest_dashboard.html`
- one image per checkpoint

## Minimal Code Reading Order

When you want to understand the project without drowning in code, read in this order:

1. `warehouse_benchmark_checkpoints.yaml`
2. `patrol_mission.launch.py`
3. `benchmark_patrol.launch.py`
4. `patrol_mission_node.cpp`
5. `inspection_at_waypoint.cpp`
6. `InspectionResult.msg`
7. `PatrolRoundSummary.msg`
8. `mission_report_node.cpp`

## Extension Workflow

### If Extending Inspection

- keep the checkpoint stop contract the same
- replace controlled labels with a real perception module gradually
- preserve saved evidence and report interfaces

### If Extending Navigation

- keep mission interfaces stable
- introduce recovery improvements carefully
- verify benchmark patrol before custom-world expansion

### If Extending Productization

- keep messages stable
- add dashboards or monitoring subscribers rather than hard-wiring more logic into control nodes

## Benchmark Run Checklist

- Build succeeded
- Runtime cleaned
- Nav2 activated
- Mission goal accepted
- Images saved
- Reports written
- Final summary matched expectations
- If visual run: Gazebo and RViz stayed up

