import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    headless = LaunchConfiguration("headless")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    gui_config_file = LaunchConfiguration("gui_config_file")
    clock_bridge_config_file = LaunchConfiguration("clock_bridge_config_file")

    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", world],
        output="screen",
    )

    gazebo_client = ExecuteProcess(
        cmd=["gz", "sim", "-g", "--gui-config", gui_config_file],
        condition=IfCondition(PythonExpression(["not ", headless])),
        output="screen",
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="world_clock_bridge",
        output="screen",
        parameters=[{
            "config_file": clock_bridge_config_file,
            "use_sim_time": use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument("headless", default_value="True"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("world"),
        DeclareLaunchArgument(
            "gui_config_file",
            default_value=os.path.join(
                get_package_share_directory("factory_inspection_mission"),
                "config",
                "benchmark_gazebo_gui.config",
            ),
        ),
        DeclareLaunchArgument(
            "clock_bridge_config_file",
            default_value=os.path.join(
                get_package_share_directory("factory_inspection_mission"),
                "config",
                "clock_bridge.yaml",
            ),
        ),
        gazebo_server,
        clock_bridge,
        TimerAction(period=2.0, actions=[gazebo_client]),
    ])
