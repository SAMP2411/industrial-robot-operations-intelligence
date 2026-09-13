# Phase 1 Navigation MVP

## Goal

Make the robot complete a patrol round reliably in simulation using Nav2 waypoint following, detect round completion in a mission node, print a summary, pause briefly, then decide whether to resend the next round.

## Start Point

- Workspace started effectively empty for this project
- No mission package yet
- No patrol logic yet
- No checkpoint YAML structure yet

## Design Choices Made In This Phase

### Loop Policy

- Chosen: `Option A`, resend one waypoint list per round
- Rejected for MVP ownership reasons: repeating a very long list upfront
- Reason:
  - round boundaries stay explicit
  - summaries become easy
  - stop conditions become easy
  - future inspection hooks fit naturally

### Language Choice

- Chosen: C++
- Reason:
  - stronger systems practice
  - better interview signal for robotics roles
  - aligns well with ROS 2 and Nav2 internals

### Round Completion Behavior

- Chosen: pause briefly after a round summary
- Reason:
  - easier to observe round boundaries during testing
  - future operator logic fits naturally here

## What Was Built

- `factory_inspection_mission` package
- Patrol mission node in C++
- Checkpoint YAML config
- Patrol launch file
- Benchmark launch file

## Key Files Added Or Established

- `src/factory_inspection_mission/src/patrol_mission_node.cpp`
- `src/factory_inspection_mission/launch/patrol_mission.launch.py`
- `src/factory_inspection_mission/launch/benchmark_patrol.launch.py`
- `src/factory_inspection_mission/config/checkpoints.yaml`
- `src/factory_inspection_mission/config/warehouse_benchmark_checkpoints.yaml`

## Core Idea

One Nav2 action goal equals one patrol round.

That means:

- the mission node owns laps
- Nav2 owns motion
- the round summary is a mission concern
- checkpoint travel is still a navigation concern

## Why An Action Client Was Used

Analogy: a service is like asking a receptionist one question and getting one reply. An action is like giving a technician a work order and getting progress updates while the job is still happening.

Where it fits:

- patrol is long-running
- we need feedback during execution
- we need a final result when the round ends

Why it exists:

- `FollowWaypoints` is not instant
- the mission layer needs progress and final status

## Verification Checkpoints

### Checkpoint 1

- Build succeeds with `colcon`
- Mission node boots and loads checkpoint YAML

### Checkpoint 2

- Mission node waits for `/follow_waypoints` instead of crashing if Nav2 is not ready

### Checkpoint 3

- Benchmark patrol completes a full round
- Round summary prints with waypoint completion

### Checkpoint 4

- Mission pauses briefly after round completion
- Round resend behavior works

## What Was Verified

- The patrol node loaded the configured checkpoint list
- The node retried gracefully while Nav2 was still activating
- A benchmark round completed successfully
- Option A resend-per-round behavior worked end to end

## New Engineering Habit Introduced Here

Benchmark-first workflow.

Instead of building a custom world immediately, the project first proved mission behavior against a known Nav2 warehouse benchmark. That reduced ambiguity early and gave a clean baseline.

## Files To Read For This Phase

- `patrol_mission_node.cpp`
- `patrol_mission.launch.py`
- `warehouse_benchmark_checkpoints.yaml`

## Interview Questions For Phase 1

### Why resend one round at a time instead of pushing repeated waypoints upfront?

- Because round ownership belongs in the mission layer.
- Because summaries and operator decisions happen at round boundaries.
- Because later inspection logic depends on explicit round completion.

### Why is an action better than a service for waypoint patrol?

- Because patrol takes time and provides feedback.
- Because we need acceptance, progress, and final result.
- Because a service does not model long-running navigation well.

