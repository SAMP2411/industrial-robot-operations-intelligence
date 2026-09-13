# Patrol Round 1 Report

- Status: SUCCESS
- Duration: 44.844 s
- Action Result: SUCCEEDED
- Nav2 Error Code: 0
- Inspections: 5
- Anomalies: 2
- Warnings: 1
- Critical: 1
- Capture Failures: 0
- Mission Decision: HOLD
- Decision Reason: A critical inspection result triggered the safety hold policy.

## Checkpoints

- [0] east_aisle | label=gauge_nominal | severity=normal | action=continue_patrol | capture_ok=true | image=/home/samarth/.ros/factory_inspection/benchmark/0000_east_aisle_gauge_nominal_11253000000.png
- [1] upper_right_turn | label=gauge_high_alarm | severity=critical | action=dispatch_operator_immediately | capture_ok=true | image=/home/samarth/.ros/factory_inspection/benchmark/0001_upper_right_turn_gauge_high_alarm_20115000000.png
- [2] upper_left_turn | label=needle_drift | severity=warning | action=schedule_recheck | capture_ok=true | image=/home/samarth/.ros/factory_inspection/benchmark/0002_upper_left_turn_needle_drift_29907000000.png
- [3] west_aisle | label=gauge_nominal | severity=normal | action=continue_patrol | capture_ok=true | image=/home/samarth/.ros/factory_inspection/benchmark/0003_west_aisle_gauge_nominal_39258000000.png
- [4] spawn_lane | label=gauge_nominal | severity=normal | action=continue_patrol | capture_ok=true | image=/home/samarth/.ros/factory_inspection/benchmark/0004_spawn_lane_gauge_nominal_48654000000.png
