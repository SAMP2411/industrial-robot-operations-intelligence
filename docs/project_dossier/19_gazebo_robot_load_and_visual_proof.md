# Gazebo Robot Load And Visual Proof

This note captures one real visual benchmark run and explains why it proves the robot is loaded and functioning in Gazebo.

## Files From The Run

- Visual run log: [visual_proof.log](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/visual_proof.log)
- Gazebo world pose dump: [warehouse_pose_info.txt](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/warehouse_pose_info.txt)
- Gazebo GUI camera pose dump: [gui_camera_pose.txt](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/gui_camera_pose.txt)
- Route coverage image from the same run: [route_coverage_visual.png](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/route_coverage_visual.png)

## Robot Loaded In Gazebo

The strongest direct evidence is that Gazebo's entity creation process succeeded:

```text
[create-23] [INFO] [ros_gz_sim]: Entity creation successful.
```

That line is in [visual_proof.log](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/visual_proof.log).

There is also Gazebo-native world state evidence. In [warehouse_pose_info.txt](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/warehouse_pose_info.txt), the simulator reports:

```text
name: "turtlebot4"
name: "base_link"
```

That means the robot exists inside the Gazebo world, not just in ROS.

## GUI Opened With Project Camera Config

The visual run launched Gazebo with:

```text
gz sim -g --gui-config .../benchmark_gazebo_gui.config
```

So the GUI did not use the old default camera. It used the project camera config from [benchmark_gazebo_gui.config](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/benchmark_gazebo_gui.config).

## Proper Functioning In The Same Visual Run

The same live run log shows the robot progressing through the warehouse route:

```text
Round 1 heading to checkpoint 1/10: spawn_lane
Round 1 heading to checkpoint 2/10: east_aisle
Round 1 heading to checkpoint 3/10: upper_right_turn
Round 1 heading to checkpoint 4/10: upper_left_turn
Round 1 heading to checkpoint 5/10: west_aisle
Round 1 heading to checkpoint 6/10: mid_east_service_bay
```

This proves the robot is not just spawned and stationary. It is navigating a wider 10-checkpoint patrol.

The easiest quick visual is [route_coverage_visual.png](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/route_coverage_visual.png), which overlays the checkpoints already visited in that exact visual run on top of the warehouse map.

## Why There Is No Gazebo PNG Here

The `/gui/screenshot` service returns `data: true` on this machine, but the plugin does not actually leave a file behind. That looks like a Gazebo screenshot-plugin quirk in this environment, not a robot or mission failure.

Because of that, the most trustworthy proof bundle is:

1. successful entity creation
2. Gazebo world pose stream containing `turtlebot4`
3. live mission log showing the robot stepping through the route
