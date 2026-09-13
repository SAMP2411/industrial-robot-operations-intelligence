# Current Topic Graph

This document records the **repo-defined message flow** that can be verified from the current source code on **Saturday, July 18, 2026**.

It focuses on topics and actions directly established by this repository. It does not attempt to fully enumerate every internal Nav2 topic.

## Core Application Message Flow

```text
latest camera image
    |
    v
inspection_at_waypoint plugin
    |
    +--> /inspection_results
    +--> /inspection_markers
    +--> inspection_log.csv + evidence images

/inspection_results
    |
    +--> patrol_mission_node
    |      aggregates round stats and decisions
    |
    +--> mission_report_node
           writes reports and dashboard artifacts

patrol_mission_node
    |
    +--> /patrol_round_summaries

/patrol_round_summaries
    |
    +--> mission_report_node
```

## Repo-Defined Topics

### `/inspection_results`

Type:

- [`factory_inspection_interfaces/msg/InspectionResult`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_interfaces/msg/InspectionResult.msg)

Produced by:

- [`inspection_at_waypoint.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp)

Consumed by:

- [`patrol_mission_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/patrol_mission_node.cpp)
- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)

### `/patrol_round_summaries`

Type:

- [`factory_inspection_interfaces/msg/PatrolRoundSummary`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_interfaces/msg/PatrolRoundSummary.msg)

Produced by:

- [`patrol_mission_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/patrol_mission_node.cpp)

Consumed by:

- [`mission_report_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/mission_report_node.cpp)

### `/inspection_markers`

Type:

- `visualization_msgs/msg/MarkerArray`

Produced by:

- [`inspection_at_waypoint.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp)

Used by:

- RViz for anomaly/review visualization

### `rgbd_camera/image`

Type:

- `sensor_msgs/msg/Image`

Consumed by:

- [`inspection_at_waypoint.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/plugins/inspection_at_waypoint.cpp)

Source:

- Gazebo camera bridge created by [`benchmark_robot_instance.launch.py`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_robot_instance.launch.py)

## Core Action Interface

### `follow_waypoints`

Type:

- `nav2_msgs/action/FollowWaypoints`

Used by:

- [`patrol_mission_node.cpp`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/src/patrol_mission_node.cpp)

Provided by:

- Nav2 waypoint follower launched during bringup

## Important Practical Note

The mission node does not drive the robot directly.

It sends one patrol round to Nav2 through the waypoint-following action and then reacts to:

- Nav2 action feedback
- Nav2 action result
- checkpoint inspection results

That boundary is important and should be preserved during future productization.
