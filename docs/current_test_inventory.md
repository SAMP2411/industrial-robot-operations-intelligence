# Current Test Inventory

This document records the actual test and verification mechanisms present in the repository on **Saturday, July 18, 2026**.

## Present Today

### 1. Build verification

Typical command:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select factory_inspection_interfaces factory_inspection_mission
```

Purpose:

- catch compile-time failures
- catch interface or dependency breakage

### 2. Runtime cleanup helper

Script:

- [`tools/clean_benchmark_runtime.sh`](/home/samarth/projects/industrial-robot-operations-intelligence/tools/clean_benchmark_runtime.sh)

Purpose:

- kill stale Gazebo/Nav2/report/bridge processes before reruns

### 3. Smoke test

Script:

- [`tools/run_iteration_smoke_test.sh`](/home/samarth/projects/industrial-robot-operations-intelligence/tools/run_iteration_smoke_test.sh)

What it currently verifies:

- benchmark launch can start
- Gazebo stays alive
- Nav2 activates
- patrol round 1 is accepted
- robot reaches checkpoint `6/10: mid_east_service_bay`

### 4. Retry-based benchmark launcher

Script:

- [`tools/run_benchmark_with_retry.sh`](/home/samarth/projects/industrial-robot-operations-intelligence/tools/run_benchmark_with_retry.sh)

Purpose:

- retry around startup flakes
- preserve log for each attempt

### 5. Regression benchmark script

Script:

- [`tools/run_benchmark_regression.sh`](/home/samarth/projects/industrial-robot-operations-intelligence/tools/run_benchmark_regression.sh)

Purpose:

- run selected benchmark seeds
- capture summary metrics from `latest_report.json`

### 6. Manual visual verification

Typical command:

```bash
ros2 launch factory_inspection_mission benchmark_patrol.launch.py headless:=False use_rviz:=False
```

Purpose:

- verify Gazebo visualization
- verify motion and route coverage
- visually inspect markers and robot behavior

### 7. Operator workflow API test

Test:

- [`test_operator_console.py`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/tests/test_operator_console.py)

Command:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
pytest fleet_api/tests/test_operator_console.py
```

What it currently verifies:

- demo-user login
- benchmark sync into SQLite
- site and asset import
- finding creation from a round report
- finding lifecycle actions
- reinspection mission creation
- evidence metadata lookup

## Not Present Yet

- C++ unit tests
- launch tests
- contract tests
- broader persistence tests
- fault-injection test suite
- endurance test harness

## Current Honest Conclusion

The repository now has one real API workflow test in addition to the ROS smoke/regression scripts, but it is still far from a full automated product test pyramid.
