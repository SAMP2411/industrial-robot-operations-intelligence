# Concepts Basic To Advanced

This document explains the main concepts used in the project in a teaching style:

- analogy
- real example
- where it fits
- why it exists

## ROS 2 Workspace

- Analogy: the workshop that holds all project parts
- Real example: `ros2_ws/` contains packages, build products, installs, and logs
- Where it fits: top-level development environment
- Why it exists: lets multiple ROS 2 packages build and work together

## ROS 2 Package

- Analogy: one toolbox with a clear purpose
- Real example: `factory_inspection_mission` contains nodes, launch files, configs, and plugin code
- Where it fits: code organization unit
- Why it exists: dependencies, build rules, and runtime resources all belong somewhere stable

## Node

- Analogy: one worker in the system
- Real example: `patrol_mission_node` owns round logic and `mission_report_node` owns report writing
- Where it fits: runtime computation unit
- Why it exists: ROS systems are built from multiple communicating processes

## Topic

- Analogy: a radio channel
- Real example: `/inspection_results` broadcasts structured inspection events
- Where it fits: asynchronous data sharing
- Why it exists: multiple components may need the same data without tight coupling

## Message

- Analogy: the shape of what is said on the radio
- Real example: `InspectionResult.msg`
- Where it fits: data contract between nodes
- Why it exists: both publisher and subscriber need the same schema

## Action

- Analogy: a work order with progress updates
- Real example: `/follow_waypoints`
- Where it fits: long-running robot tasks
- Why it exists: navigation is not a one-shot request

## Launch File

- Analogy: a conductor starting the orchestra
- Real example: `benchmark_patrol.launch.py`
- Where it fits: runtime orchestration
- Why it exists: starting Nav2, simulation, RViz, and mission nodes manually is error-prone

## YAML Config

- Analogy: a mission sheet the code can read
- Real example: `warehouse_benchmark_checkpoints.yaml`
- Where it fits: configurable inputs
- Why it exists: route and inspection expectations change more often than code

## Nav2

- Analogy: the robot’s navigation stack and driver brain
- Real example: planner, controller, AMCL, waypoint follower
- Where it fits: motion and localization
- Why it exists: mobile robots need a robust navigation pipeline, not hand-written motion logic

## Waypoint Follower

- Analogy: a route supervisor that works through a stop list
- Real example: receives the waypoint list from the mission node
- Where it fits: between mission and navigation
- Why it exists: patrol routes are more than a single pose target

## Waypoint Task Executor Plugin

- Analogy: the small job card attached to each stop
- Real example: `inspection_at_waypoint`
- Where it fits: after arrival at a waypoint
- Why it exists: checkpoint work should happen at the correct navigation moment

## TF

- Analogy: the robot’s frame relationship graph
- Real example: `map -> odom -> base_link`
- Where it fits: localization and sensor alignment
- Why it exists: robot software must know how positions relate between frames

## Map, Odom, Base Link

- `map`: global reference for long-term navigation
- `odom`: local drifting motion frame
- `base_link`: robot body frame

Real example:

- checkpoints are expressed in `map`
- controller operates using transforms through `odom`

## Lifecycle Nodes

- Analogy: equipment with controlled states like configure, activate, and shutdown
- Real example: Nav2 servers do not accept work until activated
- Where it fits: managed robot bringup
- Why it exists: robotics systems need clean startup and shutdown transitions

## QoS

- Analogy: the delivery policy for communication
- Real example: markers use transient-local durability so late RViz subscribers still get them
- Where it fits: ROS message transport behavior
- Why it exists: not all data should be treated the same way

## MarkerArray

- Analogy: pins and labels on an operator map
- Real example: critical and warning checkpoints in RViz
- Where it fits: live visualization
- Why it exists: spatial debugging is much faster than text-only debugging

## Event-Driven Architecture

- Analogy: each subsystem announces facts instead of waiting to be polled
- Real example: inspection results and round summaries are published as topics
- Where it fits: cross-layer integration
- Why it exists: reporting, dashboards, and future monitors stay decoupled from control logic

## Safety Policy

- Analogy: operations rules that sit above raw robot motion
- Real example: a critical result triggers `HOLD` even if the robot finished navigation successfully
- Where it fits: mission decision layer
- Why it exists: successful motion is not the same thing as acceptable mission outcome

## Reproducibility

- Analogy: the ability to rerun an experiment and trust the environment
- Real example: local offline world assets replaced launch-time Fuel dependency
- Where it fits: verification and reliability
- Why it exists: a benchmark that sometimes fails to start is not a good engineering benchmark

