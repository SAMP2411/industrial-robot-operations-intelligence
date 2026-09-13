# Current Launch Flow

This file explains how the current single-robot benchmark starts on **Saturday, July 18, 2026**.

## Entry Point

The main benchmark entry point is:

- [`benchmark_patrol.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_patrol.launch.py)

This launch file is the real top-level entry for the current single-robot workflow.

## Launch Sequence

### 1. Scenario generation

`benchmark_patrol.launch.py` first calls:

- [`benchmark_scenario_generator.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)

It now passes three product-foundation config sources into the generator:

- [`benchmark_site.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/sites/benchmark_site.yaml)
- [`benchmark_asset_registry.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml)
- [`benchmark_inspection_profiles.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml)

Generated outputs land under:

- `~/.ros/factory_inspection/benchmark/scenario/`

Important generated files:

- `generated_world.sdf`
- `generated_checkpoints.yaml`
- `ground_truth.yaml`
- `scenario_manifest.json`

Current improvement:

- the generated checkpoint file is no longer just a waypoint list
- it now includes site context, config provenance, and enriched asset metadata for each stop

### 2. World launch

The benchmark then includes:

- [`benchmark_world.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_world.launch.py)

This starts:

- Gazebo server
- optional Gazebo GUI
- world clock bridge

### 3. Robot launch

After the world starts, the benchmark includes:

- [`benchmark_robot_instance.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_robot_instance.launch.py)

This starts:

- `robot_state_publisher`
- Gazebo/ROS bridge nodes
- image bridges
- robot spawn process
- Nav2 bringup
- optional RViz

### 4. Mission launch

After robot and Nav2 bringup begins, the benchmark includes:

- [`patrol_mission.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/patrol_mission.launch.py)

This launches:

- `patrol_mission_node`
- `mission_report_node`

## Runtime Handoff

Once the launch sequence finishes:

1. Nav2 becomes active
2. the mission node waits for the `follow_waypoints` action
3. the mission node sends one patrol round
4. Nav2 drives the robot between checkpoints
5. the inspection plugin runs on each waypoint arrival
6. the report node writes schema-versioned artifacts from the resulting messages

## Current Visual Command

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
export FACTORY_SCENARIO_SEED=4242
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=False use_rviz:=False
```

## Current Smoke-Test Command

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
./tools/run_iteration_smoke_test.sh
```

The smoke test currently treats successful progress to checkpoint `6/10: mid_east_service_bay` as proof that the single-robot pipeline is healthy.
