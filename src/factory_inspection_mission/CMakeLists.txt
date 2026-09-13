cmake_minimum_required(VERSION 3.8)
project(factory_inspection_mission)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(factory_inspection_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_core REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(OpenCV REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(yaml_cpp_vendor REQUIRED)
find_package(yaml-cpp REQUIRED)

add_executable(patrol_mission_node src/patrol_mission_node.cpp)
ament_target_dependencies(
  patrol_mission_node
  factory_inspection_interfaces
  geometry_msgs
  nav2_msgs
  rclcpp
  rclcpp_action
)
target_link_libraries(patrol_mission_node yaml-cpp)

add_executable(mission_report_node src/mission_report_node.cpp)
ament_target_dependencies(
  mission_report_node
  factory_inspection_interfaces
  rclcpp
)

add_executable(fleet_supervisor_node src/fleet_supervisor_node.cpp)
ament_target_dependencies(
  fleet_supervisor_node
  factory_inspection_interfaces
  rclcpp
)

add_library(inspection_at_waypoint SHARED
  src/plugins/inspection_at_waypoint.cpp
)
target_include_directories(inspection_at_waypoint PUBLIC
  include
  ${OpenCV_INCLUDE_DIRS}
)
ament_target_dependencies(
  inspection_at_waypoint
  cv_bridge
  factory_inspection_interfaces
  geometry_msgs
  nav2_core
  rclcpp
  rclcpp_lifecycle
  sensor_msgs
  visualization_msgs
)
target_link_libraries(inspection_at_waypoint
  yaml-cpp
  ${OpenCV_LIBS}
)

install(TARGETS patrol_mission_node
  mission_report_node
  fleet_supervisor_node
  DESTINATION lib/${PROJECT_NAME}
)

install(TARGETS inspection_at_waypoint
  DESTINATION lib
)

install(DIRECTORY config launch worlds urdf
  DESTINATION share/${PROJECT_NAME}
)

pluginlib_export_plugin_description_file(nav2_waypoint_follower plugins.xml)

ament_package()
