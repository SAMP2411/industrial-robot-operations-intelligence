# Current Architecture

This document describes the repository as it exists on **Saturday, July 18, 2026**.

It is based on direct inspection of the repository and a successful smoke test, not on the aspirational product roadmap in `docs/advance.md`.

## System Summary

The current system is a ROS 2 Jazzy autonomous inspection benchmark built around a single mobile robot, Gazebo simulation, Nav2 waypoint navigation, checkpoint-local inspection logic, and export-style reporting.

The main flow is:

1. generate a simulated benchmark scenario
2. launch Gazebo
3. spawn a robot and bring up Nav2
4. send one patrol round at a time
5. inspect each checkpoint when reached
6. save evidence and structured inspection messages
7. generate per-round and latest-run reports
8. sync exported benchmark artifacts into a local operator database
9. review findings, evidence, and follow-up missions through a web console

## Current Runtime Layers

### 1. Scenario and Simulation Layer

Primary files:

- [`benchmark_patrol.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_patrol.launch.py)
- [`benchmark_scenario_generator.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)
- [`benchmark_world.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_world.launch.py)
- [`benchmark_site.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/sites/benchmark_site.yaml)
- [`benchmark_asset_registry.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml)
- [`benchmark_inspection_profiles.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml)

Responsibilities:

- load the benchmark site definition
- load a config-backed benchmark asset registry
- load benchmark inspection profiles and thresholds
- create randomized benchmark scenario files
- generate the world and checkpoint config
- enrich the generated route with asset metadata such as criticality, owner, profile, and viewpoint tolerance
- start Gazebo server and optional Gazebo GUI
- bridge simulation time into ROS 2

### 2. Robot Bringup Layer

Primary file:

- [`benchmark_robot_instance.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_robot_instance.launch.py)

Responsibilities:

- create the robot description via xacro
- start `robot_state_publisher`
- bridge Gazebo topics into ROS 2
- spawn the robot entity
- start Nav2 bringup
- optionally start RViz

### 3. Mission Control Layer

Primary files:

- [`patrol_mission.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/patrol_mission.launch.py)
- [`patrol_mission_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/patrol_mission_node.cpp)

Responsibilities:

- load the generated checkpoint route
- send one Nav2 `follow_waypoints` goal per mission round
- aggregate inspection results for each round
- choose round-level policy actions such as:
  - `CONTINUE`
  - `TARGETED_FOLLOW_UP`
  - `RESUME_WATCHLIST`
  - `HOLD`

### 4. Inspection Layer

Primary file:

- [`inspection_at_waypoint.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp)

Responsibilities:

- execute inspection work when Nav2 reaches a waypoint
- capture the latest camera frame
- evaluate visual and synthetic multimodal signals
- produce inspection labels, severities, confidence, and review flags
- save raw and annotated evidence images
- publish structured inspection results
- publish RViz markers

### 5. Reporting Layer

Primary file:

- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)

Responsibilities:

- subscribe to inspection results and round summaries
- write JSON, Markdown, HTML, and CSV-style exports
- generate latest-run dashboard and campaign state outputs
- append per-asset history

### 6. Operator Console Layer

Primary files:

- [`main.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/app/main.py)
- [`storage.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/app/storage.py)
- [`inspection_sync.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/app/inspection_sync.py)
- [`Fleetwatch.html`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/ui/Fleetwatch.html)

Responsibilities:

- provide authenticated tenant-scoped operator access
- persist sites, assets, missions, evidence metadata, findings, and finding events in SQLite
- sync the latest benchmark artifact set into operator-facing state
- expose operator API endpoints for findings, assets, missions, evidence, and health
- support finding lifecycle actions such as acknowledge, assign, reinspect, resolve, and close
- present a browser-based operator console with evidence preview and mission queue visibility

## Current Domain Boundaries

The current code already has useful separation:

- Nav2 owns robot movement
- the mission node owns patrol rounds and mission policy
- the waypoint plugin owns checkpoint-local inspection behavior
- the report node owns human-readable and machine-readable exports
- the FleetWatch operator layer owns persistence, operator actions, and API/UI workflow

This is the strongest architectural feature already present in the repository.

## Current Strengths

- single-robot benchmark flow works
- scenario generation is deterministic by seed
- benchmark scenario generation is now config-backed rather than purely hardcoded
- Nav2 integration is already substantial
- inspection logic is integrated into waypoint arrival
- reporting is richer than a typical demo project
- runtime JSON exports now carry explicit schema versions
- there is now a local operator API/UI MVP instead of only file outputs
- there is now SQLite-backed persistence for synced operator state
- there is already early multi-platform and fleet work in the repository

## Current Product Gaps

The current system is still route-centered and benchmark-driven in a few important ways:

- no persistent database-backed asset registry or site service
- no persistent inspection-profile administration workflow
- the ROS runtime still exports files first instead of writing live events directly into the operator store
- the operator API/UI exists, but it is still a local MVP rather than a production-hardened product surface
- the finding lifecycle exists in the operator console, but it is not yet connected back into live robot execution
- no stable integration gateway
- no full test suite beyond smoke/regression scripts

That means the repository is already a strong prototype foundation, but not yet a complete startup-grade product stack.
