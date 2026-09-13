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
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from benchmark_launch_utils import load_robot_profiles, prepare_single_robot_instance


def launch_setup(context, *args, **kwargs):
    del args
    del kwargs

    package_share = get_package_share_directory("factory_inspection_mission")
    benchmark_root = os.path.join(
        os.path.expanduser("~"),
        ".ros",
        "factory_inspection",
        "benchmark",
    )
    scenario_dir = os.path.join(benchmark_root, "scenario")
    scenario_seed = int(os.environ.get("FACTORY_SCENARIO_SEED", str(time.time_ns() % 1000000)))
    min_anomalies = int(os.environ.get("FACTORY_SCENARIO_MIN_ANOMALIES", "1"))
    max_anomalies = int(os.environ.get("FACTORY_SCENARIO_MAX_ANOMALIES", "3"))
    clutter_count = int(os.environ.get("FACTORY_SCENARIO_CLUTTER_COUNT", "10"))
    allow_critical = os.environ.get("FACTORY_SCENARIO_ALLOW_CRITICAL", "true")
    target_assets = os.environ.get("FACTORY_TARGET_ASSETS", "").strip()
    generator_script = os.path.join(package_share, "launch", "benchmark_scenario_generator.py")
    template_world = os.path.join(package_share, "worlds", "warehouse_template.sdf")
    asset_registry = os.path.join(
        package_share,
        "config",
        "assets",
        "benchmark_asset_registry.yaml",
    )
    site_config = os.path.join(
        package_share,
        "config",
        "sites",
        "benchmark_site.yaml",
    )
    inspection_profiles = os.path.join(
        package_share,
        "config",
        "inspection_profiles",
        "benchmark_inspection_profiles.yaml",
    )

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
        "--asset-registry",
        asset_registry,
        "--site-config",
        site_config,
        "--inspection-profiles",
        inspection_profiles,
    ]
    if target_assets:
        generator_command.extend(["--target-assets", target_assets])

    subprocess.run(generator_command, check=True)

    robot_profile_name = LaunchConfiguration("robot_profile").perform(context)
    robot_name = LaunchConfiguration("robot_name").perform(context)

    profiles = load_robot_profiles(os.path.join(package_share, "config", "robot_profiles.yaml"))
    if robot_profile_name not in profiles:
        known_profiles = ", ".join(sorted(profiles.keys()))
        raise RuntimeError(
            f"Unknown robot profile '{robot_profile_name}'. Known profiles: {known_profiles}")

    instance = {
        "name": robot_name,
        "namespace": "",
        "profile_name": robot_profile_name,
        "profile": profiles[robot_profile_name],
        "robot_name": f"{profiles[robot_profile_name].get('robot_name_prefix', robot_profile_name)}_{robot_name}",
        "spawn_pose": {"x": 2.12, "y": -21.30, "yaw": 1.57},
    }

    mission_config = os.path.join(scenario_dir, "generated_checkpoints.yaml")
    local_world = os.path.join(scenario_dir, "generated_world.sdf")
    prepared = prepare_single_robot_instance(
        scenario_config_path=mission_config,
        output_dir=benchmark_root,
        instance=instance,
    )

    nav2_params = PathJoinSubstitution([
        FindPackageShare("factory_inspection_mission"),
        "config",
        "warehouse_benchmark_nav2_params.yaml",
    ])
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
    configured_nav2_params = RewrittenYaml(
        source_file=nav2_params,
        param_rewrites={
            "amcl.ros__parameters.initial_pose.x": str(instance["spawn_pose"]["x"]),
            "amcl.ros__parameters.initial_pose.y": str(instance["spawn_pose"]["y"]),
            "amcl.ros__parameters.initial_pose.yaw": str(instance["spawn_pose"]["yaw"]),
            "waypoint_follower.ros__parameters.inspection_at_waypoint.mission_config_file":
                prepared["mission_config_path"],
            "waypoint_follower.ros__parameters.inspection_at_waypoint.save_dir":
                prepared["report_dir"],
        },
        convert_types=True,
    )

    nav2_map = PathJoinSubstitution([
        FindPackageShare("nav2_bringup"),
        "maps",
        "warehouse.yaml",
    ])

    world_launch = IncludeLaunchDescription(
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

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("factory_inspection_mission"),
                "launch",
                "benchmark_robot_instance.launch.py",
            ])
        ]),
        launch_arguments={
            "namespace": "",
            "use_namespace": "false",
            "use_rviz": LaunchConfiguration("use_rviz"),
            "use_sim_time": "true",
            "use_composition": "False",
            "params_file": configured_nav2_params,
            "rviz_config_file": benchmark_rviz_config,
            "map": nav2_map,
            "robot_name": prepared["robot_name"],
            "robot_profile": robot_profile_name,
            "bridge_config_file": prepared["bridge_config_path"],
            "cmd_vel_topic": prepared["topics"]["cmd_vel"],
            "odom_topic": prepared["topics"]["odom"],
            "tf_topic": prepared["topics"]["tf"],
            "joint_states_topic": prepared["topics"]["joint_states"],
            "scan_topic": prepared["topics"]["scan"],
            "imu_topic": prepared["topics"]["imu"],
            "camera_topic_base": prepared["topics"]["camera_base"],
            "camera_image_topic": prepared["topics"]["camera_image"],
            "camera_depth_topic": prepared["topics"]["camera_depth"],
            "xacro_cmd_vel_topic": prepared["sim_topics"]["cmd_vel"],
            "xacro_odom_topic": prepared["sim_topics"]["odom"],
            "xacro_tf_topic": prepared["sim_topics"]["tf"],
            "xacro_joint_states_topic": prepared["sim_topics"]["joint_states"],
            "xacro_scan_topic": prepared["sim_topics"]["scan"],
            "xacro_imu_topic": prepared["sim_topics"]["imu"],
            "xacro_camera_topic_base": prepared["sim_topics"]["camera_base"],
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
            "namespace": "",
            "config_file": prepared["mission_config_path"],
            "round_pause_seconds": LaunchConfiguration("round_pause_seconds"),
            "recovery_pause_seconds": LaunchConfiguration("recovery_pause_seconds"),
            "report_dir": prepared["report_dir"],
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

    return [
        world_launch,
        TimerAction(period=1.0, actions=[robot_launch]),
        TimerAction(period=5.0, actions=[mission_launch]),
    ]


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
        DeclareLaunchArgument("robot_profile", default_value="tb4"),
        DeclareLaunchArgument("robot_name", default_value="scout_alpha"),
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
