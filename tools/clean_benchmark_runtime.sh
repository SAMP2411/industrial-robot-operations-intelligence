#!/usr/bin/env bash

set -euo pipefail

workspace_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

patterns=(
  "ros2 launch factory_inspection_mission benchmark_patrol.launch.py"
  "gz sim"
  "/opt/ros/jazzy/lib/rviz2/rviz2"
  "/opt/ros/jazzy/lib/nav2_"
  "/opt/ros/jazzy/lib/ros_gz_"
  "parameter_bridge"
  "image_bridge"
  "/opt/ros/jazzy/lib/robot_state_publisher/robot_state_publisher"
  "${workspace_root}/install/factory_inspection_mission/lib/factory_inspection_mission/patrol_mission_node"
  "${workspace_root}/install/factory_inspection_mission/lib/factory_inspection_mission/mission_report_node"
  "patrol_mission_node"
  "mission_report_node"
  "/opt/ros/jazzy/lib/opennav_docking/opennav_docking"
)

for pattern in "${patterns[@]}"; do
  pkill -f "$pattern" 2>/dev/null || true
done

sleep 1

for pattern in "${patterns[@]}"; do
  pkill -9 -f "$pattern" 2>/dev/null || true
done
