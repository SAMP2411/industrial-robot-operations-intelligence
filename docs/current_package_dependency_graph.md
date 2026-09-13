# Current Package Dependency Graph

This document records the current package-level dependency shape of the repository on **Saturday, July 18, 2026**.

## Workspace Packages

### `factory_inspection_interfaces`

Purpose:

- custom ROS 2 message package

Direct dependencies from [`package.xml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_interfaces/package.xml):

- `ament_cmake`
- `rosidl_default_generators`
- `builtin_interfaces`
- `rosidl_default_runtime`

### `factory_inspection_mission`

Purpose:

- main simulation, mission, inspection, and reporting package

Direct dependencies from [`package.xml`](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/package.xml):

- `cv_bridge`
- `factory_inspection_interfaces`
- `geometry_msgs`
- `launch_ros`
- `nav2_bringup`
- `nav2_common`
- `nav2_core`
- `nav2_msgs`
- `nav2_minimal_tb4_description`
- `nav2_minimal_tb4_sim`
- `pluginlib`
- `rclcpp`
- `rclcpp_action`
- `rclcpp_lifecycle`
- `sensor_msgs`
- `visualization_msgs`
- `xacro`
- `yaml_cpp_vendor`

## Build-Level Graph

```text
factory_inspection_interfaces
    |
    v
factory_inspection_mission
    |
    +--> patrol_mission_node
    +--> mission_report_node
    +--> fleet_supervisor_node
    +--> inspection_at_waypoint plugin
```

## Runtime Concept Graph

```text
Gazebo / world generation
        |
        v
robot bringup + Nav2
        |
        v
patrol_mission_node
        |
        v
inspection_at_waypoint plugin
        |
        v
mission_report_node
```

## Important Architectural Observation

The repository is still compact.

That is good for the current stage because:

- domain boundaries are visible
- build complexity is still manageable
- future productization can happen deliberately instead of through accidental sprawl

The next growth step should be **clearer domain separation**, not uncontrolled package explosion.
