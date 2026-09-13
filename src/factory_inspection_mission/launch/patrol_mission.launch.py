from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    config_file = LaunchConfiguration("config_file")
    round_pause_seconds = LaunchConfiguration("round_pause_seconds")
    recovery_pause_seconds = LaunchConfiguration("recovery_pause_seconds")
    report_dir = LaunchConfiguration("report_dir")
    stop_on_failure = LaunchConfiguration("stop_on_failure")
    hold_on_severity_at_or_above = LaunchConfiguration("hold_on_severity_at_or_above")
    max_capture_failures_per_round = LaunchConfiguration("max_capture_failures_per_round")
    max_consecutive_failed_rounds = LaunchConfiguration("max_consecutive_failed_rounds")
    max_follow_up_assets = LaunchConfiguration("max_follow_up_assets")
    enable_targeted_follow_up = LaunchConfiguration("enable_targeted_follow_up")
    follow_up_round_pause_seconds = LaunchConfiguration("follow_up_round_pause_seconds")
    max_follow_up_rounds_per_campaign = LaunchConfiguration("max_follow_up_rounds_per_campaign")
    stable_follow_up_required_rounds = LaunchConfiguration("stable_follow_up_required_rounds")
    stable_follow_up_health_delta_threshold = LaunchConfiguration("stable_follow_up_health_delta_threshold")
    operator_mission_queue_file = LaunchConfiguration("operator_mission_queue_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument(
            "namespace",
            default_value="",
        ),
        DeclareLaunchArgument(
            "config_file",
            default_value=PathJoinSubstitution([
                FindPackageShare("factory_inspection_mission"),
                "config",
                "checkpoints.yaml",
            ]),
        ),
        DeclareLaunchArgument(
            "round_pause_seconds",
            default_value="3.0",
        ),
        DeclareLaunchArgument(
            "recovery_pause_seconds",
            default_value="8.0",
        ),
        DeclareLaunchArgument(
            "report_dir",
            default_value=PathJoinSubstitution([
                EnvironmentVariable("HOME"),
                ".ros",
                "factory_inspection",
                "reports",
            ]),
        ),
        DeclareLaunchArgument(
            "operator_mission_queue_file",
            default_value=PathJoinSubstitution([
                EnvironmentVariable("HOME"),
                ".ros",
                "factory_inspection",
                "operator",
                "operator_mission_queue.yaml",
            ]),
        ),
        DeclareLaunchArgument(
            "stop_on_failure",
            default_value="true",
        ),
        DeclareLaunchArgument(
            "hold_on_severity_at_or_above",
            default_value="critical",
        ),
        DeclareLaunchArgument(
            "max_capture_failures_per_round",
            default_value="1",
        ),
        DeclareLaunchArgument(
            "max_consecutive_failed_rounds",
            default_value="2",
        ),
        DeclareLaunchArgument(
            "max_follow_up_assets",
            default_value="3",
        ),
        DeclareLaunchArgument(
            "enable_targeted_follow_up",
            default_value="true",
        ),
        DeclareLaunchArgument(
            "follow_up_round_pause_seconds",
            default_value="2.0",
        ),
        DeclareLaunchArgument(
            "max_follow_up_rounds_per_campaign",
            default_value="2",
        ),
        DeclareLaunchArgument(
            "stable_follow_up_required_rounds",
            default_value="1",
        ),
        DeclareLaunchArgument(
            "stable_follow_up_health_delta_threshold",
            default_value="2.0",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
        ),
        Node(
            package="factory_inspection_mission",
            executable="patrol_mission_node",
            name="patrol_mission_node",
            namespace=namespace,
            output="screen",
            parameters=[{
                "config_file": config_file,
                "round_pause_seconds": round_pause_seconds,
                "recovery_pause_seconds": recovery_pause_seconds,
                "stop_on_failure": stop_on_failure,
                "hold_on_severity_at_or_above": hold_on_severity_at_or_above,
                "max_capture_failures_per_round": max_capture_failures_per_round,
                "max_consecutive_failed_rounds": max_consecutive_failed_rounds,
                "max_follow_up_assets": max_follow_up_assets,
                "enable_targeted_follow_up": enable_targeted_follow_up,
                "follow_up_round_pause_seconds": follow_up_round_pause_seconds,
                "max_follow_up_rounds_per_campaign": max_follow_up_rounds_per_campaign,
                "stable_follow_up_required_rounds": stable_follow_up_required_rounds,
                "stable_follow_up_health_delta_threshold": stable_follow_up_health_delta_threshold,
                "operator_mission_queue_file": operator_mission_queue_file,
                "use_sim_time": use_sim_time,
            }],
        ),
        Node(
            package="factory_inspection_mission",
            executable="mission_report_node",
            name="mission_report_node",
            namespace=namespace,
            output="screen",
            parameters=[{
                "report_dir": report_dir,
                "use_sim_time": use_sim_time,
            }],
        ),
    ])
