# Find The Robot Quickly

## What Changed

The benchmark now uses a more visible TurtleBot model with a bright finder beacon and a closer Gazebo startup camera.

Relevant files:

- Visible robot model: [turtlebot4_benchmark_visible.urdf.xacro](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/urdf/turtlebot4_benchmark_visible.urdf.xacro)
- Gazebo camera config: [benchmark_gazebo_gui.config](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/benchmark_gazebo_gui.config)
- Sim launch using that model: [benchmark_tb4_local_sim.launch.py](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_tb4_local_sim.launch.py)

## Exact Commands

Run these in `/home/samarth/projects/industrial-robot-operations-intelligence`:

```bash
source /opt/ros/jazzy/setup.bash
source /home/samarth/projects/industrial-robot-operations-intelligence/install/setup.bash
./tools/clean_benchmark_runtime.sh
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=False use_rviz:=False
```

## What You Should See

When Gazebo opens:

- look in the lower warehouse area first
- the robot starts near `spawn_lane`
- the robot should now have a tall bright orange finder beacon above it
- the first motion should be:
  - `spawn_lane`
  - then `east_aisle`
  - then `upper_right_turn`

Use this map-style helper image before launching:

- [visual_beacon_route.png](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/visual_beacon_route.png)

That image shows the startup area and the first verified route segment.

## Verified Proof

From the latest successful visual run in [visual_beacon_run.log](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/visual_beacon_run.log):

```text
Entity creation successful.
Round 1 heading to checkpoint 1/10: spawn_lane
Inspection saved at checkpoint spawn_lane ...
Round 1 heading to checkpoint 2/10: east_aisle
```

The visible robot model also really contains the beacon:

```text
finder_beacon_joint
finder_beacon_link
finder_mast
```

Those were verified from the expanded URDF during the build step.

## If You Still Don’t See It

Use this mental model:

- the robot does not start in the middle of the warehouse
- it starts in the lower warehouse near `spawn_lane`
- the bright orange beacon is the easiest thing to spot first

If the window still feels zoomed out, focus only on the lower warehouse first and ignore the upper shelves until you see the orange beacon moving.
