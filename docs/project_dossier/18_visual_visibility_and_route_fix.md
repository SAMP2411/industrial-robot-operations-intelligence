# Visual Visibility And Route Fix

## What Was Wrong

Two different problems made Gazebo hard to trust visually:

- the camera could open on an unhelpful default view, so the robot was easy to miss
- the patrol route only covered a tight lower-warehouse loop, so it did not look like a full inspection mission

There was also a hidden runtime issue:

- stale `gz sim` processes from older runs were surviving cleanup and contaminating new launches

## What Changed

- Gazebo now launches with a project-owned GUI config in [benchmark_gazebo_gui.config](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/config/benchmark_gazebo_gui.config)
- the local sim launcher now starts the GUI with `--gui-config` in [benchmark_tb4_local_sim.launch.py](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_tb4_local_sim.launch.py)
- the randomized benchmark route now spans 10 checkpoints across lower, middle, and upper warehouse sections in [benchmark_scenario_generator.py](/home/samarth/projects/industrial-robot-operations-intelligence/src/factory_inspection_mission/launch/benchmark_scenario_generator.py)
- cleanup now kills any lingering `gz sim` process, not just the old path pattern, in [clean_benchmark_runtime.sh](/home/samarth/projects/industrial-robot-operations-intelligence/tools/clean_benchmark_runtime.sh)

## Verified Evidence

The live visual run log is copied here:

- [visual_route_fix.log](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/visual_route_fix.log)

The generated route used by that run is copied here:

- [generated_checkpoints_visual.yaml](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/assets/current_run/generated_checkpoints_visual.yaml)

Key verified lines from the visual run:

```text
Round 1 heading to checkpoint 1/10: spawn_lane
Round 1 heading to checkpoint 2/10: east_aisle
Round 1 heading to checkpoint 3/10: upper_right_turn
Round 1 heading to checkpoint 4/10: upper_left_turn
Round 1 heading to checkpoint 5/10: west_aisle
Round 1 heading to checkpoint 6/10: mid_east_service_bay
```

That is enough to confirm the robot is no longer stuck in a tiny lower-corner demo loop.
