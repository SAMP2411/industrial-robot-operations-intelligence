import os
import subprocess
import sys
import time
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
    UnsetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from benchmark_launch_utils import DEFAULT_FLEET_SPECS, load_robot_profiles, parse_robot_specs, prepare_fleet_instances


def launch_setup(context, *args, **kwargs):
    del args
    del kwargs

    package_share = get_package_share_directory("factory_inspection_mission")
    fleet_root = os.path.join(
        os.path.expanduser("~"),
        ".ros",
        "factory_inspection",
        "fleet",
    )
    scenario_dir = os.path.join(fleet_root, "scenario")
    scenario_seed = int(os.environ.get("FACTORY_SCENARIO_SEED", str(time.time_ns() % 1000000)))
    min_anomalies = int(os.environ.get("FACTORY_SCENARIO_MIN_ANOMALIES", "1"))
    max_anomalies = int(os.environ.get("FACTORY_SCENARIO_MAX_ANOMALIES", "3"))
    clutter_count = int(os.environ.get("FACTORY_SCENARIO_CLUTTER_COUNT", "10"))
    allow_critical = os.environ.get("FACTORY_SCENARIO_ALLOW_CRITICAL", "true")
    target_assets = os.environ.get("FACTORY_TARGET_ASSETS", "").strip()
    generator_script = os.path.join(package_share, "launch", "benchmark_scenario_generator.py")
    template_world = os.path.join(package_share, "worlds", "warehouse_template.sdf")

    generator_command = [
        "python3",
        generator_script,
        "--output-dir",
        scenario_dir,
        "--template-world",
        template_world,
        "--seed",
        str(scenario_seed),
        "--min-anomalies",
        str(min_anomalies),
        "--max-anomalies",
        str(max_anomalies),
        "--clutter-count",
        str(clutter_count),
        "--allow-critical",
        allow_critical,
    ]
    if target_assets:
        generator_command.extend(["--target-assets", target_assets])

    subprocess.run(generator_command, check=True)

    profiles = load_robot_profiles(os.path.join(package_share, "config", "robot_profiles.yaml"))
    fleet_specs = LaunchConfiguration("fleet_robots").perform(context)
    instances = parse_robot_specs(fleet_specs, profiles)

    scenario_config_path = os.path.join(scenario_dir, "generated_checkpoints.yaml")
    prepared_fleet = prepare_fleet_instances(
        scenario_config_path=scenario_config_path,
        output_dir=fleet_root,
        instances=instances,
    )

    benchmark_rviz_config = PathJoinSubstitution([
        FindPackageShare("factory_inspection_mission"),
        "config",
        "benchmark_patrol.rviz",
    ])
    benchmark_gui_config = PathJoinSubstitution([
        FindPackageShare("factory_inspection_mission"),
        "config",
        "benchmark_gazebo_gui.config",
    ])
    nav2_map = PathJoinSubstitution([
        FindPackageShare("nav2_bringup"),
        "maps",
        "warehouse.yaml",
    ])
    nav2_params = PathJoinSubstitution([
        FindPackageShare("factory_inspection_mission"),
        "config",
        "warehouse_benchmark_nav2_params.yaml",
    ])
    local_world = os.path.join(scenario_dir, "generated_world.sdf")

    actions = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("factory_inspection_mission"),
                    "launch",
                    "benchmark_world.launch.py",
                ])
            ]),
            launch_arguments={
                "headless": LaunchConfiguration("headless"),
                "use_sim_time": "true",
                "world": local_world,
                "gui_config_file": benchmark_gui_config,
            }.items(),
        )
    ]

    for index, instance in enumerate(prepared_fleet["instances"]):
        configured_nav2_params = RewrittenYaml(
            source_file=nav2_params,
            param_rewrites={
                "amcl.ros__parameters.initial_pose.x": str(instance["spawn_pose"]["x"]),
                "amcl.ros__parameters.initial_pose.y": str(instance["spawn_pose"]["y"]),
                "amcl.ros__parameters.initial_pose.yaw": str(instance["spawn_pose"]["yaw"]),
                "waypoint_follower.ros__parameters.inspection_at_waypoint.mission_config_file":
                    instance["mission_config_path"],
                "waypoint_follower.ros__parameters.inspection_at_waypoint.save_dir":
                    instance["report_dir"],
            },
            convert_types=True,
        )

        robot_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("factory_inspection_mission"),
                    "launch",
                    "benchmark_robot_instance.launch.py",
                ])
            ]),
            launch_arguments={
                "namespace": instance["namespace"],
                "use_namespace": "true",
                "use_rviz": LaunchConfiguration("use_rviz") if index == 0 else "false",
                "use_sim_time": "true",
                "use_composition": "False",
                "params_file": configured_nav2_params,
                "rviz_config_file": benchmark_rviz_config,
                "map": nav2_map,
                "robot_name": instance["robot_name"],
                "robot_profile": instance["profile_name"],
                "bridge_config_file": instance["bridge_config_path"],
                "cmd_vel_topic": instance["topics"]["cmd_vel"],
                "odom_topic": instance["topics"]["odom"],
                "tf_topic": instance["topics"]["tf"],
                "joint_states_topic": instance["topics"]["joint_states"],
                "scan_topic": instance["topics"]["scan"],
                "imu_topic": instance["topics"]["imu"],
                "camera_topic_base": instance["topics"]["camera_base"],
                "camera_image_topic": instance["topics"]["camera_image"],
                "camera_depth_topic": instance["topics"]["camera_depth"],
                "xacro_cmd_vel_topic": instance["sim_topics"]["cmd_vel"],
                "xacro_odom_topic": instance["sim_topics"]["odom"],
                "xacro_tf_topic": instance["sim_topics"]["tf"],
                "xacro_joint_states_topic": instance["sim_topics"]["joint_states"],
                "xacro_scan_topic": instance["sim_topics"]["scan"],
                "xacro_imu_topic": instance["sim_topics"]["imu"],
                "xacro_camera_topic_base": instance["sim_topics"]["camera_base"],
                "x_pose": str(instance["spawn_pose"]["x"]),
                "y_pose": str(instance["spawn_pose"]["y"]),
                "yaw": str(instance["spawn_pose"]["yaw"]),
            }.items(),
        )

        mission_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("factory_inspection_mission"),
                    "launch",
                    "patrol_mission.launch.py",
                ])
            ]),
            launch_arguments={
                "namespace": instance["namespace"],
                "config_file": instance["mission_config_path"],
                "round_pause_seconds": LaunchConfiguration("round_pause_seconds"),
                "recovery_pause_seconds": LaunchConfiguration("recovery_pause_seconds"),
                "report_dir": instance["report_dir"],
                "stop_on_failure": LaunchConfiguration("stop_on_failure"),
                "hold_on_severity_at_or_above": LaunchConfiguration("hold_on_severity_at_or_above"),
                "max_capture_failures_per_round": LaunchConfiguration("max_capture_failures_per_round"),
                "max_consecutive_failed_rounds": LaunchConfiguration("max_consecutive_failed_rounds"),
                "max_follow_up_assets": LaunchConfiguration("max_follow_up_assets"),
                "enable_targeted_follow_up": LaunchConfiguration("enable_targeted_follow_up"),
                "follow_up_round_pause_seconds": LaunchConfiguration("follow_up_round_pause_seconds"),
                "max_follow_up_rounds_per_campaign": LaunchConfiguration("max_follow_up_rounds_per_campaign"),
                "stable_follow_up_required_rounds": LaunchConfiguration("stable_follow_up_required_rounds"),
                "stable_follow_up_health_delta_threshold": LaunchConfiguration("stable_follow_up_health_delta_threshold"),
                "use_sim_time": "true",
            }.items(),
        )

        actions.append(
            TimerAction(
                period=1.0 + float(index) * 10.0,
                actions=[robot_launch],
            )
        )
        actions.append(
            TimerAction(
                period=7.0 + float(index) * 10.0,
                actions=[mission_launch],
            )
        )

    actions.append(
        Node(
            package="factory_inspection_mission",
            executable="fleet_supervisor_node",
            name="fleet_supervisor_node",
            output="screen",
            parameters=[{
                "robot_names": [instance["name"] for instance in prepared_fleet["instances"]],
                "report_dir": fleet_root,
                "use_sim_time": True,
            }],
        )
    )

    return actions


def generate_launch_description():
    benchmark_assets = PathJoinSubstitution([
        FindPackageShare("factory_inspection_mission"),
        "worlds",
        "benchmark_assets",
    ])
    tb4_description_resources = PathJoinSubstitution([
        FindPackageShare("nav2_minimal_tb4_description"),
        "..",
    ])

    return LaunchDescription([
        UnsetEnvironmentVariable("LIBGL_ALWAYS_SOFTWARE"),
        UnsetEnvironmentVariable("QT_OPENGL"),
        DeclareLaunchArgument("use_rviz", default_value="False"),
        DeclareLaunchArgument("headless", default_value="True"),
        DeclareLaunchArgument("fleet_robots", default_value=DEFAULT_FLEET_SPECS),
        DeclareLaunchArgument("round_pause_seconds", default_value="3.0"),
        DeclareLaunchArgument("recovery_pause_seconds", default_value="8.0"),
        DeclareLaunchArgument("stop_on_failure", default_value="true"),
        DeclareLaunchArgument("hold_on_severity_at_or_above", default_value="critical"),
        DeclareLaunchArgument("max_capture_failures_per_round", default_value="1"),
        DeclareLaunchArgument("max_consecutive_failed_rounds", default_value="2"),
        DeclareLaunchArgument("max_follow_up_assets", default_value="3"),
        DeclareLaunchArgument("enable_targeted_follow_up", default_value="true"),
        DeclareLaunchArgument("follow_up_round_pause_seconds", default_value="2.0"),
        DeclareLaunchArgument("max_follow_up_rounds_per_campaign", default_value="2"),
        DeclareLaunchArgument("stable_follow_up_required_rounds", default_value="1"),
        DeclareLaunchArgument("stable_follow_up_health_delta_threshold", default_value="2.0"),
        SetEnvironmentVariable(
            name="GZ_SIM_RESOURCE_PATH",
            value=[
                benchmark_assets,
                ":",
                tb4_description_resources,
                ":",
                EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value=""),
            ],
        ),
        SetEnvironmentVariable(
            name="IGN_GAZEBO_RESOURCE_PATH",
            value=[
                benchmark_assets,
                ":",
                tb4_description_resources,
                ":",
                EnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", default_value=""),
            ],
        ),
        OpaqueFunction(function=launch_setup),
    ])
