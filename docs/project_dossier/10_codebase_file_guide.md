# Codebase File Guide

This file explains the role of each key file, why it exists, and when to read it.

## Message Package

### `src/factory_inspection_interfaces/msg/InspectionResult.msg`

- Purpose: structured output of one checkpoint inspection
- Read it when: you want to know what the inspection plugin publishes
- Why it matters: it defines the contract between inspection and reporting

### `src/factory_inspection_interfaces/msg/PatrolRoundSummary.msg`

- Purpose: structured output of one patrol round
- Read it when: you want to understand round-level policy inputs and reporting
- Why it matters: this is the round boundary contract

## Launch Files

### `src/factory_inspection_mission/launch/patrol_mission.launch.py`

- Purpose: start the mission node and report node
- Read it when: you want to understand runtime parameters for the mission layer
- Why it matters: this is the clean entry point for mission-only bringup

### `src/factory_inspection_mission/launch/benchmark_patrol.launch.py`

- Purpose: launch simulation, Nav2, RViz, and mission together
- Read it when: you want the full benchmark story
- Why it matters: this is the main demo command

## Config Files

### `src/factory_inspection_mission/config/checkpoints.yaml`

- Purpose: default checkpoint config
- Read it when: you want the general mission format

### `src/factory_inspection_mission/config/warehouse_benchmark_checkpoints.yaml`

- Purpose: benchmark route and controlled inspection states
- Read it when: you want to see the benchmark truth table

### `src/factory_inspection_mission/config/warehouse_benchmark_nav2_params.yaml`

- Purpose: benchmark Nav2 parameters and waypoint plugin configuration
- Read it when: you want to know how the plugin is wired into Nav2

### `src/factory_inspection_mission/config/benchmark_patrol.rviz`

- Purpose: the RViz layout used for visual verification
- Read it when: you want to know which displays are preloaded

## Mission Layer

### `src/factory_inspection_mission/src/patrol_mission_node.cpp`

- Purpose: round orchestration, action client logic, inspection aggregation, mission policy
- Read it when: you want to understand the highest-level control logic
- Key ideas inside:
  - checkpoint loading
  - round start
  - Nav2 action callbacks
  - inspection result subscription
  - round synchronization delay
  - `CONTINUE` / `RECOVERY_RETRY` / `HOLD`

## Inspection Layer

### `src/factory_inspection_mission/include/factory_inspection_mission/inspection_at_waypoint.hpp`

- Purpose: plugin interface and data structure definitions
- Read it when: you want the class shape before reading the implementation

### `src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp`

- Purpose: checkpoint capture, classification stub, CSV writing, marker publishing, inspection event publishing
- Read it when: you want to understand what happens at waypoint arrival
- Key ideas inside:
  - YAML metadata lookup
  - image capture
  - severity handling
  - marker style selection
  - legacy CSV rotation

### `src/factory_inspection_mission/plugins.xml`

- Purpose: pluginlib registration for Nav2
- Read it when: you want to know how Nav2 finds the waypoint task executor

## Reporting Layer

### `src/factory_inspection_mission/src/mission_report_node.cpp`

- Purpose: subscribe to inspection and summary topics, then write JSON, Markdown, and HTML outputs
- Read it when: you want to understand the productization layer
- Key ideas inside:
  - delayed report scheduling
  - checkpoint aggregation
  - artifact generation
  - HTML dashboard rendering

## Simulation Reliability

### `src/factory_inspection_mission/worlds/warehouse_offline.sdf`

- Purpose: fully local benchmark world for reliable visual simulation
- Read it when: you want to understand the reproducibility fix

### `src/factory_inspection_mission/worlds/benchmark_assets/`

- Purpose: local model assets used by the offline world
- Read it when: you want to see how the Fuel dependency was removed
- Note: these are vendored benchmark assets for reproducibility, not original project-authored geometry

## Build And Package Files

### `src/factory_inspection_mission/CMakeLists.txt`

- Purpose: build targets, dependencies, install rules, plugin installation
- Read it when: you need to change executables, libraries, or installed runtime resources

### `src/factory_inspection_mission/package.xml`

- Purpose: package metadata and ROS dependency declarations
- Read it when: you add dependencies or need to explain package structure

## Runtime Support

### `tools/clean_benchmark_runtime.sh`

- Purpose: kill stale benchmark processes after interrupted runs
- Read it when: a relaunch behaves strangely

## Living Notes

### `docs/engineering_manual.md`

- Purpose: continuously updated project manual
- Read it when: you want a shorter running guide than this dossier

## Recommended Code Dive Order

1. `warehouse_benchmark_checkpoints.yaml`
2. `benchmark_patrol.launch.py`
3. `patrol_mission_node.cpp`
4. `inspection_at_waypoint.cpp`
5. `InspectionResult.msg`
6. `PatrolRoundSummary.msg`
7. `mission_report_node.cpp`
8. `warehouse_offline.sdf`

