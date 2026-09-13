# Phase 2 Inspection MVP

## Goal

Upgrade the patrol from “visit waypoints” to “visit checkpoints and do work at arrival”.

The thin slice for this phase was:

`stop -> capture -> classify -> save -> continue`

## Core Design Decision

Checkpoint-local behavior should run in a Nav2 waypoint task executor plugin, not inside the mission node.

## Why This Was The Right Fit

Analogy: Nav2 is the driver that gets the robot to the address. The waypoint task executor is the technician who performs the on-site inspection once the robot arrives.

Where it fits:

- right after waypoint arrival
- before moving to the next checkpoint

Why it exists:

- arrival is a navigation concern
- inspection-at-arrival is checkpoint-local behavior
- keeping that logic in the plugin avoids a second messy state machine

## What Was Built

- Nav2 waypoint task executor plugin
- checkpoint metadata in YAML
- saved image artifacts at each waypoint
- CSV inspection log
- controlled anomaly labeling

## Key Files

- `src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp`
- `src/factory_inspection_mission/include/factory_inspection_mission/inspection_at_waypoint.hpp`
- `src/factory_inspection_mission/config/warehouse_benchmark_nav2_params.yaml`
- `src/factory_inspection_mission/config/warehouse_benchmark_checkpoints.yaml`
- `src/factory_inspection_mission/plugins.xml`

## Controlled Inspection Strategy

The project deliberately did not start with a real gauge classifier. Instead, the checkpoint YAML carried controlled labels such as:

- `gauge_nominal`
- `gauge_high_alarm`
- `needle_drift`

Why this was the correct MVP move:

- it isolated mission integration from perception uncertainty
- it made testing repeatable
- it let inspection, reporting, and visualization be built before real CV

## What The Plugin Does

1. Receives waypoint arrival from Nav2
2. Looks up checkpoint metadata from YAML
3. Captures an image from the camera topic
4. Saves the image
5. Writes a CSV row
6. Publishes a structured inspection event
7. Publishes live RViz markers for non-normal states
8. Returns control to waypoint following

## What Was Verified

- Five images were saved in the benchmark artifact folder
- The checkpoint labels matched the YAML config
- The critical anomaly was recorded at `upper_right_turn`
- The warning checkpoint was recorded at `upper_left_turn`
- The patrol still completed a full round while inspection was active

## Important Insight

This phase changed the project from a navigation demo to a mission demo. The robot no longer just moves. It performs work at each stop.

## Verification Artifacts Produced

- saved PNG image per checkpoint
- `inspection_log.csv`
- terminal logs confirming inspection results

## Why Checkpoint Metadata Lives In YAML

- waypoint order and inspection meaning stay in one source of truth
- debugging is easier
- changing the benchmark does not require recompiling code
- future upgrades can add camera settings, dwell time, and expected target type

## Interview Questions For Phase 2

### Why is the waypoint task executor cleaner than doing inspection inside the mission node?

- Because the plugin runs exactly at waypoint arrival.
- Because Nav2 already owns arrival semantics.
- Because the mission node should own rounds, not per-waypoint inspection internals.

### Why start with controlled labels instead of a real classifier?

- Because system integration should become reliable before perception becomes complex.
- Because repeatability matters during early verification.
- Because controlled labels make failures easier to localize.

