import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    bringup_dir = get_package_share_directory("nav2_bringup")
    launch_dir = os.path.join(bringup_dir, "launch")
    sim_dir = get_package_share_directory("nav2_minimal_tb4_sim")
    desc_dir = get_package_share_directory("nav2_minimal_tb4_description")
    mission_dir = get_package_share_directory("factory_inspection_mission")

    slam = LaunchConfiguration("slam")
    namespace = LaunchConfiguration("namespace")
    use_namespace = LaunchConfiguration("use_namespace")
    map_yaml_file = LaunchConfiguration("map")
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    autostart = LaunchConfiguration("autostart")
    use_composition = LaunchConfiguration("use_composition")
    use_respawn = LaunchConfiguration("use_respawn")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    use_simulator = LaunchConfiguration("use_simulator")
    use_robot_state_pub = LaunchConfiguration("use_robot_state_pub")
    use_rviz = LaunchConfiguration("use_rviz")
    headless = LaunchConfiguration("headless")
    world = LaunchConfiguration("world")
    gui_config_file = LaunchConfiguration("gui_config_file")
    robot_name = LaunchConfiguration("robot_name")
    robot_sdf = LaunchConfiguration("robot_sdf")

    pose = {
        "x": LaunchConfiguration("x_pose", default="2.12"),
        "y": LaunchConfiguration("y_pose", default="-21.30"),
        "z": LaunchConfiguration("z_pose", default="0.01"),
        "R": LaunchConfiguration("roll", default="0.00"),
        "P": LaunchConfiguration("pitch", default="0.00"),
        "Y": LaunchConfiguration("yaw", default="1.57"),
    }

    remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    start_robot_state_publisher_cmd = Node(
        condition=IfCondition(use_robot_state_pub),
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=namespace,
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "robot_description": Command(["xacro", " ", robot_sdf]),
        }],
        remappings=remappings,
    )

    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "rviz_launch.py")),
        condition=IfCondition(use_rviz),
        launch_arguments={
            "namespace": namespace,
            "use_namespace": use_namespace,
            "use_sim_time": use_sim_time,
            "rviz_config": rviz_config_file,
        }.items(),
    )

    bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "bringup_launch.py")),
        launch_arguments={
            "namespace": namespace,
            "use_namespace": use_namespace,
            "slam": slam,
            "map": map_yaml_file,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": autostart,
            "use_composition": use_composition,
            "use_respawn": use_respawn,
        }.items(),
    )

    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", world],
        condition=IfCondition(use_simulator),
        output="screen",
    )

    gazebo_client = ExecuteProcess(
        cmd=["gz", "sim", "-g", "--gui-config", gui_config_file],
        condition=IfCondition(PythonExpression([use_simulator, " and not ", headless])),
        output="screen",
    )

    gz_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(sim_dir, "launch", "spawn_tb4.launch.py")),
        launch_arguments={
            "namespace": namespace,
            "use_simulator": use_simulator,
            "use_sim_time": use_sim_time,
            "robot_name": robot_name,
            "x_pose": pose["x"],
            "y_pose": pose["y"],
            "z_pose": pose["z"],
            "roll": pose["R"],
            "pitch": pose["P"],
            "yaw": pose["Y"],
        }.items(),
    )

    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        str(Path(desc_dir).parent.resolve()),
    )

    return LaunchDescription([
        DeclareLaunchArgument("namespace", default_value=""),
        DeclareLaunchArgument("use_namespace", default_value="false"),
        DeclareLaunchArgument("slam", default_value="False"),
        DeclareLaunchArgument("map", default_value=os.path.join(bringup_dir, "maps", "warehouse.yaml")),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(bringup_dir, "params", "nav2_params.yaml"),
        ),
        DeclareLaunchArgument("autostart", default_value="true"),
        DeclareLaunchArgument("use_composition", default_value="False"),
        DeclareLaunchArgument("use_respawn", default_value="False"),
        DeclareLaunchArgument(
            "rviz_config_file",
            default_value=os.path.join(bringup_dir, "rviz", "nav2_default_view.rviz"),
        ),
        DeclareLaunchArgument("use_simulator", default_value="True"),
        DeclareLaunchArgument("use_robot_state_pub", default_value="True"),
        DeclareLaunchArgument("use_rviz", default_value="True"),
        DeclareLaunchArgument("headless", default_value="True"),
        DeclareLaunchArgument("world"),
        DeclareLaunchArgument("robot_name", default_value="nav2_turtlebot4"),
        DeclareLaunchArgument(
            "robot_sdf",
            default_value=os.path.join(mission_dir, "urdf", "turtlebot4_benchmark_visible.urdf.xacro"),
        ),
        DeclareLaunchArgument("x_pose", default_value="2.12"),
        DeclareLaunchArgument("y_pose", default_value="-21.30"),
        DeclareLaunchArgument("z_pose", default_value="0.01"),
        DeclareLaunchArgument("roll", default_value="0.00"),
        DeclareLaunchArgument("pitch", default_value="0.00"),
        DeclareLaunchArgument("yaw", default_value="1.57"),
        DeclareLaunchArgument(
            "gui_config_file",
            default_value=os.path.join(
                get_package_share_directory("factory_inspection_mission"),
                "config",
                "benchmark_gazebo_gui.config",
            ),
        ),
        set_env_vars_resources,
        gazebo_server,
        TimerAction(period=2.0, actions=[gazebo_client]),
        TimerAction(period=2.0, actions=[gz_robot]),
        start_robot_state_publisher_cmd,
        rviz_cmd,
        bringup_cmd,
    ])
