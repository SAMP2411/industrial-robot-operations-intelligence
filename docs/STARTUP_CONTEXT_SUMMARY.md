# Startup Context Summary

This document is the plain-language handoff for this project as of **Saturday, July 18, 2026**.

Use it when you want to brief:

- another AI chat
- a mentor
- a teammate
- a startup planning session
- an interviewer

without forcing them to read the whole repository first.

## 1. Project In One Sentence

This project is a ROS 2 + Nav2 autonomous factory inspection robot system that launches a warehouse simulation, sends a robot through asset checkpoints, performs inspection at each stop, saves evidence, and generates mission-level reports and decisions.

## 2. What Has Been Achieved So Far

The project is already beyond a simple robot demo.

Right now it can:

- launch a factory-style Gazebo simulation
- spawn a mobile inspection robot
- run Nav2 for waypoint navigation
- patrol a multi-checkpoint route
- stop and inspect at each checkpoint
- save raw and annotated evidence images
- classify synthetic benchmark anomalies
- publish RViz inspection markers
- write JSON, Markdown, CSV, and HTML outputs
- make round-level decisions like `CONTINUE`, `TARGETED_FOLLOW_UP`, `RESUME_WATCHLIST`, and `HOLD`

New progress in this iteration:

- the benchmark is now driven by a config-backed site definition
- the benchmark is now driven by a config-backed asset registry
- the benchmark is now driven by config-backed inspection profiles
- generated scenario files now preserve config provenance
- key JSON outputs now include explicit schema versions
- the repo now has an audit-and-phase-report documentation structure tied to real verification
- the repo now includes a FleetWatch-based operator console with SQLite persistence
- findings can now be acknowledged, assigned, queued for reinspection, resolved, and closed through an authenticated API/UI
- operator-created missions now dispatch back into the live ROS patrol loop through a shared mission queue file
- reinspection and manual inspection missions now carry mission identity all the way into ROS round reports and dashboard exports
- benchmark sync now reuses operator mission IDs instead of creating duplicate mission records after execution

## 3. The Core Idea

The easiest way to picture the system is this:

1. describe the site and the assets
2. generate a patrol scenario
3. launch the world and the robot
4. move to each inspection point
5. inspect what is there
6. record evidence and findings
7. decide what the mission should do next

So the robot is not just “driving around.”

It is running a full inspection workflow.

## 4. What The Project Is Trying To Become

The long-term goal from [`advance.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/advance.md) is a startup-grade industrial inspection platform that can:

- manage sites and assets
- schedule inspections
- direct one or more robots
- collect multimodal evidence
- create findings
- support operator review
- track history over time
- integrate with industrial systems

Today the project is still simulation-first, but it already has the shape of that product.

## 5. Why The New Config Layer Matters

This is an important design improvement.

Before, the benchmark was much closer to “a smart hardcoded demo route.”

Now we have explicit files for:

- site definition:
  [`benchmark_site.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/sites/benchmark_site.yaml)
- asset registry:
  [`benchmark_asset_registry.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml)
- inspection profiles:
  [`benchmark_inspection_profiles.yaml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml)

That means the system now knows more than “go to waypoint A, then B.”

It also knows:

- which site it is in
- which asset each checkpoint belongs to
- how critical that asset is
- who owns that asset operationally
- which inspection profile applies
- what viewpoint/tolerance metadata belongs to that stop

This is closer to how a real startup product thinks: assets first, route second.

## 6. End-To-End Workflow

This is the current runtime story in simple order.

### Step 1: Start the benchmark

Main entry point:

- [`benchmark_patrol.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_patrol.launch.py)

This is the top-level single-robot mission launch.

### Step 2: Load product-style config and generate the scenario

Scenario generation happens in:

- [`benchmark_scenario_generator.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)

It reads:

- site config
- asset registry
- inspection profile config

Then it generates:

- the world description
- the checkpoint list
- the synthetic ground truth
- the scenario manifest

### Step 3: Launch the world

World launch happens in:

- [`benchmark_world.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_world.launch.py)

This starts Gazebo and the simulation clock bridge.

### Step 4: Spawn the robot and bring up Nav2

Robot bringup happens in:

- [`benchmark_robot_instance.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_robot_instance.launch.py)

This handles:

- robot description
- state publishing
- Gazebo/ROS bridging
- robot spawn
- Nav2 bringup
- optional RViz

### Step 5: Launch mission control

Mission launch happens in:

- [`patrol_mission.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/patrol_mission.launch.py)

It launches:

- `patrol_mission_node`
- `mission_report_node`

It also points both the operator console and the mission node at the same local dispatch file:

- `~/.ros/factory_inspection/operator/operator_mission_queue.yaml`

That file is the current bridge between the product layer and the robot layer.

### Step 6: Accept operator-requested missions between rounds

Operator workflow happens in:

- [`main.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/app/main.py)
- [`operator_dispatch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/app/operator_dispatch.py)

What happens:

- a user creates a manual inspection or reinspection mission in FleetWatch
- FleetWatch stores it in SQLite for the UI
- FleetWatch also writes it to the shared operator mission queue file
- `patrol_mission_node` checks that queue before launching the next normal round
- if the queued mission maps cleanly to real checkpoint assets, the robot executes it as the next round
- when that round ends, the mission result is written back into the queue and back into FleetWatch state
- the round report now includes `mission_id`, `mission_source`, and `mission_type`

Important current behavior:

- operator missions are inserted **between rounds**
- they do **not** yet interrupt a live Nav2 round that is already underway

### Step 7: Send one patrol round at a time

Mission logic lives in:

- [`patrol_mission_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/patrol_mission_node.cpp)

This node:

- waits for Nav2 waypoint follower
- sends one round
- optionally claims the next queued operator mission
- tracks checkpoint results
- decides whether to continue, hold, or follow up

### Step 8: Inspect at each waypoint

Inspection logic lives in:

- [`inspection_at_waypoint.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp)

This node/plugin path handles:

- image capture
- anomaly-style classification
- confidence and severity assignment
- evidence saving
- RViz marker publishing
- structured inspection result publishing

### Step 9: Generate reports and campaign state

Reporting logic lives in:

- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)

It writes:

- per-round reports
- latest report outputs
- dashboard state
- campaign state
- history artifacts

## 7. Architecture In One View

The current system is best understood as six layers:

### 1. Scenario / Simulation layer

- site config
- asset registry
- inspection profile config
- world generation
- Gazebo launch

### 2. Navigation layer

- Nav2 planning
- controller behavior
- waypoint following

### 3. Mission layer

- round ownership
- patrol submission
- follow-up and hold decisions

### 4. Inspection layer

- checkpoint-local sensing
- anomaly-style evaluation
- evidence generation

### 5. Reporting layer

- exports
- dashboards
- campaign state
- human-readable summaries

### 6. Operator layer

- authenticated FastAPI service
- SQLite-backed operator state
- benchmark artifact sync
- findings queue
- mission dispatch queue shared with ROS
- evidence preview

## 8. Why The Architecture Is Strong

The strongest design decision in the repo is separation of responsibilities:

- Nav2 owns movement
- the mission node owns patrol rounds and decisions
- the inspection plugin owns what happens at a checkpoint
- the report node owns outputs
- the new config files own site/asset/profile definition
- the FleetWatch operator layer owns persistence and operator-facing workflow

That is valuable because it lets us improve one layer without rewriting the whole system.

Example:

- better perception later does not require rewriting Nav2
- a future operator API does not require rewriting Gazebo bringup
- a future database can replace YAML configs without deleting the current benchmark

## 9. What Files The System Generates

Runtime artifacts mainly go under:

- `/home/samarth/.ros/factory_inspection/benchmark`

### Scenario outputs

- `generated_world.sdf`
- `generated_checkpoints.yaml`
- `ground_truth.yaml`
- `scenario_manifest.json`

### Evidence outputs

- raw images
- annotated images

### Structured outputs

- `inspection_log.csv`
- `latest_report.json`
- `latest_report.md`
- `latest_dashboard.html`
- `latest_dashboard_state.json`
- `latest_campaign_state.json`
- `asset_history.csv`
- `round_000X_report.json`
- `round_000X_report.md`
- `round_000X_report.html`

### Visualization outputs

- Gazebo robot/world visualization
- RViz anomaly markers
- dossier screenshots and copied artifacts
- FleetWatch operator console UI

## 10. What The Robot Is Detecting Right Now

The current benchmark supports anomaly-style outputs such as:

- `asset_nominal`
- `roller_imbalance`
- `gas_leak_detected`
- `unconfirmed_visual_finding`

It also supports:

- severity levels
- confidence values
- review-required logic
- targeted follow-up decisions

So it is already expressing richer operational meaning than a simple pass/fail demo.

## 11. What Is Real Vs What Is Still Simulated

### Real engineering pieces already in place

- ROS 2 node architecture
- launch system
- Nav2 integration
- Gazebo simulation
- waypoint patrol logic
- config-backed asset/site/profile layer
- checkpoint inspection hook
- evidence saving
- structured reporting
- dashboard artifact generation
- mission policy logic
- multi-round behavior
- authenticated operator API/UI
- SQLite persistence for operator-side missions, findings, evidence metadata, and sync history
- live operator-to-robot mission dispatch through the shared queue bridge

### Still benchmark-grade or simulated

- anomaly generation is still synthetic benchmark logic
- perception is not yet a plant-validated industrial vision stack
- some classifications are heuristic or controlled
- multi-robot support exists in the repo, but is not yet the hardened main path
- findings and evidence still sync from exported benchmark artifacts instead of a live event bus
- operator missions are live-dispatched through a shared queue file, but active rounds are not yet preempted mid-navigation
- the operator console is still a local MVP, not a production deployment surface

## 12. What Was Verified

Phase 0 baseline verification proved:

- the benchmark launches
- Nav2 becomes active
- the mission node can submit a patrol round
- the robot progresses through the route

Phase 1 foundation verification proved:

- config-backed scenario generation builds successfully
- the benchmark still runs with the new config inputs
- generated checkpoint and scenario files include schema/version metadata
- report exports include explicit schema versions

Latest operator-bridge verification proved:

- FleetWatch mission creation writes into the shared operator mission queue
- queue state can be synced back into SQLite-backed mission state
- ROS message/report builds still succeed after adding operator mission identity fields

Primary proof references:

- [`phase_00_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_00_report.md)
- [`phase_01_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_01_report.md)
- [`phase_04_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_04_report.md)

## 13. Why This Matters For A Startup Plan

This repo is already useful for startup planning because it demonstrates:

- a real robotics software pipeline
- a modular autonomy architecture
- asset-linked inspection logic
- evidence generation
- decision-making behavior
- product-style output contracts

That makes it much stronger than a normal portfolio robot demo.

## 14. Honest Current Limitations

The main current limitations are:

- perception is still benchmark-grade
- some anomaly generation is synthetic
- asset and inspection-profile truth is still YAML-based, not service-backed
- the operator workflow is local MVP quality rather than production-hardened
- the operator mission bridge is still file-backed rather than service-backed
- findings/evidence ingest is still import-based rather than live event streaming
- multi-robot and multi-platform paths are not yet the main verified path

These are good next startup engineering phases, not signs that the project is weak.

## 15. Best Next Product Steps

If we continue advancing toward startup-grade depth, the highest-value next moves are:

- persistent asset, mission, evidence, and finding storage
- a formal finding model and finding lifecycle
- replace the file-backed operator mission bridge with a live service or event bus
- stream findings/evidence directly instead of relying on export import
- stronger multimodal inspection skill contracts
- asset-centered mission planning beyond route-first generation
- regression tests that protect schemas and mission behavior

## 16. Short Summary To Paste Into Another AI Chat

```text
I am building a ROS 2 + Nav2 autonomous factory inspection robot project. The system launches a warehouse simulation in Gazebo, spawns a robot, generates a scenario, sends the robot through asset-linked checkpoints, performs inspection at each waypoint, saves raw and annotated evidence images, publishes structured inspection results and RViz markers, and generates JSON/CSV/Markdown/HTML reports plus mission-level decisions like CONTINUE, TARGETED_FOLLOW_UP, RESUME_WATCHLIST, and HOLD. The architecture is separated into scenario/simulation, navigation, mission, inspection, reporting, and operator layers. Nav2 owns movement, the mission node owns round-level decisions, the inspection plugin owns checkpoint inspection, the report node owns output artifacts, and FleetWatch owns operator-facing persistence and workflow. In the latest progress, the benchmark was upgraded from a mostly hardcoded route into a config-backed product foundation with a site definition, asset registry, inspection profiles, schema-versioned scenario artifacts, schema-versioned JSON report outputs, and a live operator mission bridge where manual inspection and reinspection missions created in FleetWatch are written to a shared queue and then executed by the ROS patrol node between rounds. Round reports now carry mission_id, mission_source, and mission_type so operator-triggered execution can be traced end to end. The system is already strong as an end-to-end robotics software workflow, while perception and anomaly intelligence remain benchmark-grade rather than plant-validated.
```

## 17. Final Takeaway

This project is currently a real autonomous inspection software pipeline prototype with an emerging product data model.

It is no longer just:

- a Gazebo demo
- a waypoint script
- an image saver

It is a layered robotics system that:

- defines a site
- defines assets
- generates a mission scenario
- runs a robot through the patrol
- inspects those assets
- stores evidence
- reports findings
- makes mission-level decisions

That is exactly why it is a strong foundation for startup analysis and portfolio storytelling.
