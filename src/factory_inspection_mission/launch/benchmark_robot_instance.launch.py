import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bringup_dir = get_package_share_directory("nav2_bringup")
    launch_dir = os.path.join(bringup_dir, "launch")
    mission_dir = get_package_share_directory("factory_inspection_mission")

    namespace = LaunchConfiguration("namespace")
    use_namespace = LaunchConfiguration("use_namespace")
    slam = LaunchConfiguration("slam")
    map_yaml_file = LaunchConfiguration("map")
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    autostart = LaunchConfiguration("autostart")
    use_composition = LaunchConfiguration("use_composition")
    use_respawn = LaunchConfiguration("use_respawn")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    use_robot_state_pub = LaunchConfiguration("use_robot_state_pub")
    use_rviz = LaunchConfiguration("use_rviz")
    robot_name = LaunchConfiguration("robot_name")
    robot_sdf = LaunchConfiguration("robot_sdf")
    robot_profile = LaunchConfiguration("robot_profile")
    bridge_config_file = LaunchConfiguration("bridge_config_file")
    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    tf_topic = LaunchConfiguration("tf_topic")
    joint_states_topic = LaunchConfiguration("joint_states_topic")
    scan_topic = LaunchConfiguration("scan_topic")
    imu_topic = LaunchConfiguration("imu_topic")
    camera_topic_base = LaunchConfiguration("camera_topic_base")
    camera_image_topic = LaunchConfiguration("camera_image_topic")
    camera_depth_topic = LaunchConfiguration("camera_depth_topic")
    xacro_cmd_vel_topic = LaunchConfiguration("xacro_cmd_vel_topic")
    xacro_odom_topic = LaunchConfiguration("xacro_odom_topic")
    xacro_tf_topic = LaunchConfiguration("xacro_tf_topic")
    xacro_joint_states_topic = LaunchConfiguration("xacro_joint_states_topic")
    xacro_scan_topic = LaunchConfiguration("xacro_scan_topic")
    xacro_imu_topic = LaunchConfiguration("xacro_imu_topic")
    xacro_camera_topic_base = LaunchConfiguration("xacro_camera_topic_base")
    pose = {
        "x": LaunchConfiguration("x_pose", default="2.12"),
        "y": LaunchConfiguration("y_pose", default="-21.30"),
        "z": LaunchConfiguration("z_pose", default="0.01"),
        "R": LaunchConfiguration("roll", default="0.00"),
        "P": LaunchConfiguration("pitch", default="0.00"),
        "Y": LaunchConfiguration("yaw", default="1.57"),
    }

    remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    robot_description_content = Command([
        "xacro ",
        robot_sdf,
        " platform_profile:=",
        robot_profile,
        " cmd_vel_topic:=",
        xacro_cmd_vel_topic,
        " odom_topic:=",
        xacro_odom_topic,
        " tf_topic:=",
        xacro_tf_topic,
        " joint_states_topic:=",
        xacro_joint_states_topic,
        " scan_topic:=",
        xacro_scan_topic,
        " imu_topic:=",
        xacro_imu_topic,
        " camera_topic_base:=",
        xacro_camera_topic_base,
    ])

    start_robot_state_publisher_cmd = Node(
        condition=IfCondition(use_robot_state_pub),
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=namespace,
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "robot_description": robot_description_content,
        }],
        remappings=remappings,
    )

    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="bridge_ros_gz",
        namespace=namespace,
        output="screen",
        parameters=[{
            "config_file": bridge_config_file,
            "use_sim_time": use_sim_time,
        }],
    )

    camera_bridge_image = Node(
        package="ros_gz_image",
        executable="image_bridge",
        name="bridge_gz_ros_camera_image",
        namespace=namespace,
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
        }],
        arguments=[camera_image_topic],
    )

    camera_bridge_depth = Node(
        package="ros_gz_image",
        executable="image_bridge",
        name="bridge_gz_ros_camera_depth",
        namespace=namespace,
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
        }],
        arguments=[camera_depth_topic],
    )

    spawn_model = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        namespace=namespace,
        output="screen",
        arguments=[
            "-entity", robot_name,
            "-topic", "robot_description",
            "-robot_namespace", namespace,
            "-x", pose["x"], "-y", pose["y"], "-z", pose["z"],
            "-R", pose["R"], "-P", pose["P"], "-Y", pose["Y"],
        ],
        parameters=[{"use_sim_time": use_sim_time}],
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

    delayed_spawn = TimerAction(
        period=1.0,
        actions=[spawn_model],
    )

    delayed_bringup = TimerAction(
        period=3.0,
        actions=[bringup_cmd, rviz_cmd],
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
        DeclareLaunchArgument("use_robot_state_pub", default_value="True"),
        DeclareLaunchArgument("use_rviz", default_value="False"),
        DeclareLaunchArgument("robot_name", default_value="inspection_robot"),
        DeclareLaunchArgument("robot_profile", default_value="tb4"),
        DeclareLaunchArgument(
            "robot_sdf",
            default_value=os.path.join(mission_dir, "urdf", "inspection_platform.urdf.xacro"),
        ),
        DeclareLaunchArgument("bridge_config_file"),
        DeclareLaunchArgument("cmd_vel_topic", default_value="/cmd_vel"),
        DeclareLaunchArgument("odom_topic", default_value="/odom"),
        DeclareLaunchArgument("tf_topic", default_value="/tf"),
        DeclareLaunchArgument("joint_states_topic", default_value="/joint_states"),
        DeclareLaunchArgument("scan_topic", default_value="/scan"),
        DeclareLaunchArgument("imu_topic", default_value="/imu"),
        DeclareLaunchArgument("camera_topic_base", default_value="/rgbd_camera"),
        DeclareLaunchArgument("camera_image_topic", default_value="/rgbd_camera/image"),
        DeclareLaunchArgument("camera_depth_topic", default_value="/rgbd_camera/depth_image"),
        DeclareLaunchArgument("xacro_cmd_vel_topic", default_value="/cmd_vel"),
        DeclareLaunchArgument("xacro_odom_topic", default_value="/odom"),
        DeclareLaunchArgument("xacro_tf_topic", default_value="tf"),
        DeclareLaunchArgument("xacro_joint_states_topic", default_value="joint_states"),
        DeclareLaunchArgument("xacro_scan_topic", default_value="/scan"),
        DeclareLaunchArgument("xacro_imu_topic", default_value="/imu"),
        DeclareLaunchArgument("xacro_camera_topic_base", default_value="/rgbd_camera"),
        DeclareLaunchArgument("x_pose", default_value="2.12"),
        DeclareLaunchArgument("y_pose", default_value="-21.30"),
        DeclareLaunchArgument("z_pose", default_value="0.01"),
        DeclareLaunchArgument("roll", default_value="0.00"),
        DeclareLaunchArgument("pitch", default_value="0.00"),
        DeclareLaunchArgument("yaw", default_value="1.57"),
        start_robot_state_publisher_cmd,
        bridge_node,
        camera_bridge_image,
        camera_bridge_depth,
        delayed_spawn,
        delayed_bringup,
    ])
